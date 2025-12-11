import io
import os
import sys
import asyncio
import traceback
import torch
import numpy as np
import soundfile as sf
from fastapi import FastAPI, HTTPException
from fastapi.responses import StreamingResponse
from pydantic import BaseModel
from typing import Optional

# =======================================================
# 1. 配置与初始化
# =======================================================
app = FastAPI(title="Chatterbox Server (Dynamic Voice)")
gpu_lock = asyncio.Lock()

print("⏳ 正在初始化模型...")
device = "cuda" if torch.cuda.is_available() else "cpu"
print(f"🚀 使用设备: {device}")

chat = None

# 加载模型
try:
    from chatterbox import ChatterboxTTS
    print("⏳ 正在加载模型 (from_pretrained)...")
    chat = ChatterboxTTS.from_pretrained(device=device)
    print("✅ 模型加载成功！")
except ImportError:
    print("❌ 无法导入 ChatterboxTTS")
    sys.exit(1)

# 寻找核心方法
if not hasattr(chat, 'prepare_conditionals') or not hasattr(chat, 'generate'):
    print("❌ 致命错误：此版本的 Chatterbox 不支持 prepare_conditionals/generate 流程")
    sys.exit(1)

# =======================================================
# 2. 后台任务 (支持动态音色路径)
# =======================================================
def _sync_inference_task(text, voice_path, seed, output_format):
    """
    运行在独立线程中的推理任务
    """
    # 1. 检查音色文件是否存在
    if not os.path.exists(voice_path):
        raise FileNotFoundError(f"服务端未找到音色文件: {voice_path}")

    if seed:
        torch.manual_seed(int(seed))
        np.random.seed(int(seed))
        
    try:
        # 2. 准备音色条件 (读取指定的 voice_path)
        # Fast分支逻辑: prepare_conditionals(wav_fpath=...)
        conds = chat.prepare_conditionals(wav_fpath=voice_path)
        
        # 3. 生成音频
        try:
            # 尝试标准调用: generate(text, conds)
            wavs = chat.generate(text, conds)
        except TypeError:
            try:
                wavs = chat.generate([text], conds)
            except TypeError:
                wavs = chat.generate(text=text, conditionals=conds)

        # 4. 后处理
        if isinstance(wavs, tuple): wavs = wavs[0]
        if isinstance(wavs, list) and len(wavs) > 0: wavs = wavs[0]
        if isinstance(wavs, torch.Tensor): wavs = wavs.cpu().numpy()
        
        audio_data = np.array(wavs).flatten()
        
        # 5. 导出
        buffer = io.BytesIO()
        fmt = "WAV" if output_format.lower() == "wav" else "MP3"
        sf.write(buffer, audio_data, 24000, format=fmt)
        buffer.seek(0)
        return buffer, fmt

    except Exception as e:
        print(f"❌ 推理错误: {e}")
        traceback.print_exc()
        raise e

# =======================================================
# 3. API 接口
# =======================================================
class TTSRequest(BaseModel):
    text: str
    voice_path: str = "voices/Jordan.wav" # 默认值，客户端可以覆盖
    seed: Optional[int] = None
    output_format: str = "mp3"

@app.post("/tts")
async def tts_endpoint(req: TTSRequest):
    async with gpu_lock:
        loop = asyncio.get_running_loop()
        try:
            buffer, fmt = await loop.run_in_executor(
                None, 
                _sync_inference_task, 
                req.text, req.voice_path, req.seed, req.output_format
            )
            media_type = "audio/wav" if fmt == "WAV" else "audio/mpeg"
            return StreamingResponse(buffer, media_type=media_type)
        except FileNotFoundError as e:
            raise HTTPException(404, str(e))
        except Exception as e:
            raise HTTPException(500, f"Generation Error: {str(e)}")

if __name__ == "__main__":
    import uvicorn
    # 依然推荐多 worker
    uvicorn.run(app, host="0.0.0.0", port=8004)
