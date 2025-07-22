# Models Directory

This directory contains the Whisper model files used for transcription.

## Automatic Download

Models are automatically downloaded during installation:

```bash
./scripts/install_and_test.sh
```

## Manual Download

If you need to download models manually:

```bash
# Base model (recommended for most use cases)
wget https://huggingface.co/ggerganov/whisper.cpp/resolve/main/ggml-base.bin -O models/ggml-base.bin

# Or other models:
# wget https://huggingface.co/ggerganov/whisper.cpp/resolve/main/ggml-tiny.bin -O models/ggml-tiny.bin
# wget https://huggingface.co/ggerganov/whisper.cpp/resolve/main/ggml-small.bin -O models/ggml-small.bin
# wget https://huggingface.co/ggerganov/whisper.cpp/resolve/main/ggml-medium.bin -O models/ggml-medium.bin
# wget https://huggingface.co/ggerganov/whisper.cpp/resolve/main/ggml-large-v3.bin -O models/ggml-large-v3.bin
```

## Model Sizes

| Model | Size | Speed | Quality |
|-------|------|-------|---------|
| tiny | 39 MB | Fastest | Basic |
| base | 142 MB | Fast | Good |
| small | 244 MB | Medium | Better |
| medium | 769 MB | Slow | Very Good |
| large | 1.5 GB | Slowest | Best |

## Configuration

Set the model path in your `.env` file:

```bash
WHISPER_MODEL_PATH=./models/ggml-base.bin
```

## Note

- Model files are excluded from git due to their large size
- The installation script automatically downloads the base model
- Choose smaller models for faster processing on limited hardware
- Choose larger models for better transcription quality