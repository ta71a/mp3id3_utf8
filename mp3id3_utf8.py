# mp3のid3タグをUTF-8に変更するスクリプト。引数で指定したディレクトリ以下を再帰的にたどってmp3を探す
# https://www.it-mure.jp.net/ja/linux/id3タグのエンコーディングを修復する/957037725/
# でbobinceという人が載せたスクリプトに変更を加えた
# Usage:
# python mp3id3_utf8.py /media/mp3_dir

# cp932 はSJIS, CP1252はLatin-1相当
# ここに列挙した文字コードを順番に試して、変換できたら採用する。いずれも変換できなければ例外を出す
tryencodings= 'cp932', 'cp1252'

import os
import mutagen.id3
import sys
import logging


logging.basicConfig(filename='conv.log', level=logging.INFO)

def findMP3s(path):
    logging.debug('findMp3: ' + path)
    for child in os.listdir(path):
        child= os.path.join(path, child)
        if os.path.isdir(child):
            for mp3 in findMP3s(child):
                yield mp3
        elif child.decode('utf8').lower().endswith(u'.mp3'):
            yield child

for path in findMP3s(sys.argv[1]):
    logging.debug('Mp3 path: ' + path)
    try:
        id3= mutagen.id3.ID3(path)
    except:
        logging.info("mutagen could not open: " + path)
        continue

    to_save = False
    for key, value in id3.items():
        logging.debug("key: " + key)
        if hasattr(value, "encoding") and hasattr(value, "text") and value.encoding!=3 and len(value.text) > 0 and isinstance(getattr(value, 'text', [None])[0], unicode):

            if value.encoding==0:
                correct_enc = None
                org_text = '\n'.join(value.text)
                bytes= org_text.encode('iso-8859-1')
                has_changed = False

                for encoding in tryencodings:
                    try:
                        decoded_text = bytes.decode(encoding)
                    except:
                        pass
                    else:
                        correct_enc = encoding
                        logging.debug("correct_enc: " + correct_enc + "\norg_text: " + org_text + "\ndecoded_text: " + decoded_text)
                        if decoded_text != org_text:
                            has_changed = True
                        break
                else:
                    raise ValueError('None of the tryencodings work for %r key %r' % (path, key))

                if has_changed:
                    if isinstance(value.text, unicode):
                        value.text = value.text.encode('iso-8859-1').decode(correct_enc)
                        logging.info("decode(" + correct_enc + "): " + value.text)
                    else:
                        for i in range(len(value.text)):
                            value.text[i]= value.text[i].encode('iso-8859-1').decode(correct_enc)
                            logging.info("decode(" + correct_enc + "): " + value.text[i])

                    value.encoding= 3
                    to_save = True

    if to_save:
        logging.info("saving changes to: " + path)
        id3.save()
