"""Small live provider check, without exposing credentials or reasoning."""
import json,time
from pathlib import Path
import minimax_dialogue as api
from performance_jobs import ROOT,write
def main():
 dest=ROOT/'.cache/minimax-check';dest.mkdir(exist_ok=True);start=time.monotonic()
 result=api.reply([],'今天工作好累，想休息一下。');chat_s=time.monotonic()-start
 start=time.monotonic();voice=api.speak(result['reply'],result['intent'],dest/'speech.mp3')
 report={'reply':result['reply'],'intent':result['intent'],'chat_model':result['model'],'chat_s':round(chat_s,3),'speech_s':round(time.monotonic()-start,3),'voice':voice}
 write(dest/'result.json',report);print(json.dumps(report,ensure_ascii=True))
if __name__=='__main__':main()
