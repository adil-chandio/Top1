"""Text-only editorial checks, not science/retention/voice approval."""
import json
from pathlib import Path
import re
BASE=Path(__file__).parent

def words(text):
    return re.findall(r"\b[\w]+(?:[-’'][\w]+)*\b", text, re.UNICODE)

def narration(version):
    text=(BASE/f'SCRIPT_DRAFT_{version}_ROMAN_URDU.md').read_text()
    if version=='V2':
        assert text.count('<!-- NARRATION_START -->')==1
        assert text.count('<!-- NARRATION_END -->')==1
        text=text.split('<!-- NARRATION_START -->')[1].split('<!-- NARRATION_END -->')[0]
    else:
        text=text.split('\n---\n')[1]
        text=re.sub(r'\[[^\]]*\]', '', text, flags=re.S)
    return '\n'.join(line for line in text.splitlines() if not line.startswith('#'))

def main():
    a,b=narration('V1'),narration('V2')
    counts={'v1':len(words(a)),'v2':len(words(b))}
    assert counts['v2']>0
    v2=(BASE/'SCRIPT_DRAFT_V2_ROMAN_URDU.md').read_text()
    assert all(f'## {i} —' in v2 for i in range(1,7))
    for token in ['C01','C02','C03','C04','C06','C07','C08','C09']:
        assert token in v2,token
    report={'counting':'Unicode word tokens; exclude headings, bracketed stage notes and QA; not spoken syllables','narration_word_tokens':counts,'change_tokens':counts['v2']-counts['v1'],'change_percent':round(100*(counts['v2']-counts['v1'])/counts['v1'],1),'checks_passed':['six editorial sections present','explicit narration boundaries','expected factual trace IDs present'],'limits':['No audio generated or timed','No retention measurement','Citation presence is not verification of truth','Token reduction is not proof of better script','No automated semantic originality certification']}
    (BASE/'data/script_edit_receipt.json').write_text(json.dumps(report,indent=2))
    print(json.dumps(report,indent=2))
if __name__=='__main__':main()
