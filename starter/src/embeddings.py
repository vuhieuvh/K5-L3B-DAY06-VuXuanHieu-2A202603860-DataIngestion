"""Local semantic embeddings with explicit E5 task prefixes."""
from pathlib import Path
from fastembed import TextEmbedding
from fastembed.common.model_description import ModelSource, PoolingType

MODEL = "intfloat/multilingual-e5-small"
DIMENSIONS = 384
MODEL_FILE = "onnx/model_qint8_avx512_vnni.onnx"


def load_embedder(cache: Path) -> TextEmbedding:
    if MODEL not in {entry["model"] for entry in TextEmbedding.list_supported_models()}:
        TextEmbedding.add_custom_model(
            model=MODEL, pooling=PoolingType.MEAN, normalization=True,
            sources=ModelSource(hf=MODEL), dim=DIMENSIONS, model_file=MODEL_FILE,
        )
    return TextEmbedding(model_name=MODEL, specific_model_path=str(cache), threads=4)


