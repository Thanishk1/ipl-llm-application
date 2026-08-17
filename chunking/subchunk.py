from sentence_transformers import SentenceTransformer
import json

model = SentenceTransformer('all-MiniLM-L6-v2')
tokenizer = model.tokenizer
MAX_TOKENS = 256

def split_sentences(text):
    return text.split(". ")

def count_tokens(text):
    return len(tokenizer.encode(text))
def subchunk_if_needed(chunk, max_tokens=MAX_TOKENS):
    prefix = f"{chunk['season']} {chunk['team1']} vs {chunk['team2']} {chunk['subheading']} "
    budget = max_tokens - count_tokens(prefix)  # tokens available for content alone

    if count_tokens(prefix + chunk['content']) <= max_tokens:
        new_chunk = dict(chunk)
        new_chunk['sub_index'] = 0
        return [new_chunk]

    # Step 1: split on the REAL paragraph separator (single \n), sentence-split any oversized piece,
    # and hard word-split as a last resort so nothing ever slips through unchecked.
    pieces = []
    for para in chunk['content'].split('\n'):
        para = para.strip()
        if not para:
            continue
        if count_tokens(para) <= budget:
            pieces.append(para)
        else:
            for sent in split_sentences(para):
                sent = sent.strip()
                if not sent:
                    continue
                if count_tokens(sent) <= budget:
                    pieces.append(sent)
                else:
                    words, buf = sent.split(), []
                    for w in words:
                        buf.append(w)
                        if count_tokens(" ".join(buf)) > budget:
                            buf.pop()
                            pieces.append(" ".join(buf))
                            buf = [w]
                    if buf:
                        pieces.append(" ".join(buf))

    # Step 2: greedy-pack, with overlap only added when it actually still fits
    sub_chunks = []
    current_text = ""
    for piece in pieces:
        candidate = (current_text + " " + piece).strip() if current_text else piece
        if current_text and count_tokens(candidate) > budget:
            sub_chunks.append(current_text)
            overlap_sentences = split_sentences(current_text)
            overlap = overlap_sentences[-1] if overlap_sentences else ""
            current_text = piece
            if overlap and count_tokens(overlap + " " + piece) <= budget:
                current_text = (overlap + " " + piece).strip()
        else:
            current_text = candidate
    if current_text:
        sub_chunks.append(current_text)

    result = []
    for i, text in enumerate(sub_chunks):
        new_chunk = dict(chunk)
        new_chunk['content'] = text
        new_chunk['sub_index'] = i
        result.append(new_chunk)
    return result
with open("chunked_reports_enriched.json", "r", encoding="utf-8") as f:
    all_chunks = json.load(f)

final_chunks = []
for c in all_chunks:
    final_chunks.extend(subchunk_if_needed(c))

print("Original chunks:", len(all_chunks))
print("Final chunks after subchunking:", len(final_chunks))

over_limit = sum(1 for c in final_chunks
                  if count_tokens(f"{c['season']} {c['team1']} vs {c['team2']} {c['subheading']} {c['content']}") > MAX_TOKENS)
print("Still over limit after subchunking:", over_limit)

with open("final_chunks.json", "w", encoding="utf-8") as f:
    json.dump(final_chunks, f, indent=2, ensure_ascii=False)