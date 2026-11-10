import json
from app.evaluation import evaluate
if __name__=='__main__': print(json.dumps(evaluate(),indent=2,ensure_ascii=False))
