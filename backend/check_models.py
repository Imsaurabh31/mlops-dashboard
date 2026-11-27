"""Quick check — verify backend imports and model files are found."""
from app.main import app
from app.services.inference_service import model_status, _load_session

print(f'Backend OK — {len(app.routes)} routes')
print()
print('Model status:')
status = model_status()
for k, v in status.items():
    print(f'  {k}: exists={v["exists"]} size={v["size_mb"]}MB')

# Try loading the staff model
print()
print('Loading staff (atto) model...')
sess = _load_session('staff')
if sess:
    print('  Loaded OK — input:', sess.get_inputs()[0].shape, 'output:', sess.get_outputs()[0].shape)
else:
    print('  Could not load (onnxruntime may be unavailable)')

print()
print('Real training script available:', __import__('pathlib').Path('scripts/training_scripts/train_and_evaluate.py').exists())
