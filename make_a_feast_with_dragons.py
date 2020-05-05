from ebooklib import epub
import csv


rom_d = {'I': 1, 'II': 2, 'III': 3, 'IV': 4, 'V': 5, 'VI': 6, 'VII': 7,
         'VIII': 8, 'IX': 9, 'X': 10, 'XI': 11, 'XII': 12, 'XIII': 13}

roman_numerals = list(rom_d.keys())

def parse_chapters(filename='A Feast With Dragons.csv', rn=roman_numerals):
    ch_list = []
    with open(filename) as f:
        reader = csv.reader(f)
        for row in reader:
            ch_list.append(row)
    ch_d = {}
    names = []
    for ncb in ch_list:
        # ncb == ['N. TITLE', 'BOOK']
        nc, b = ncb
        n = nc.split('.')[0]
        c = nc.split('.')[1].strip()
        ch_d[n] = {'chapter': c, 'book': b}
        # c == 'NAME ROMAN_NUMERAL' or 'WORD WORD ... WORD'
        nn = c.split(' ')[0].lower()
        rr = c.split(' ')[-1]
        if any([r == rr for r in rn]) and nn not in names:
            names.append(nn)
    return ch_d, names


def initialize_new_book():
    new_book = epub.EpubBook()
    new_book.set_identifier('23skidoo')
    new_book.set_title('A Feast with Dragons')
    new_book.set_language('en')
    new_book.add_author('George R. R. Martin')
    descrip = 'A Song of Ice and Fire books ' + \
              '4 and 5 with chapters interleaved ' + \
              'according to the A Feast with ' + \
              'Dragons specification'
    new_book.add_metadata('DC', 'description', descrip)
    return new_book


def parse_book(filename, chapter_title_marks, names):
    # markers for finding chapter title
    pre, post = chapter_title_marks
    delta = len(pre)

    book = epub.read_epub(filename)

    # for name-numbered chapters
    name_count = {}
    for n in names:
        name_count[n] = 0

    chapters = {}
    for item in book.get_items():
        ss = item.content
        i = ss.find(pre)
        if i > 0: # a chapter with a regularly formatted chapter title
            j = ss[i:].find(post)
            title = ss[i+delta:i+j].lower().replace(b'\xe2\x80\x99', b"'")
            if title in names: # name + number chapter
                if name_count[title] == 0:
                    chapters[title] = {}
                name_count[title] += 1
                this_count = name_count[title]
            else: # other chapter
                chapters[title] = {}
                this_count = 0
            chapters[title][this_count] = {}
            chapters[title][this_count]['name'] = item.get_name()
            content = b'<html>' + item.get_body_content() + b'</html>'
            chapters[title][this_count]['content'] = content

    css = book.get_item_with_id('css')

    return chapters, css


if __name__ == "__main__":
            
    # AFFC chapter title marker and filename
    AFFC_mk = b'<h3 class="calibre5">', b'</h3>'
    AFFC_fn = 'ASOIAF_4_A_Feast_for_Crows.epub'

    # ADWD chapter title marker and filename
    ADWD_mk = b'<span class="calibre18">', b'</span>'
    ADWD_fn = 'ASOIAF_5_A_Dance_with_Dragons.epub'

    # AFWD chapter list, names that need roman numerals
    chapter_d, names_s = parse_chapters()
    names_b = [n.encode() for n in names_s]

    # parse original ebooks, make a big dictionary
    AFFC_ch, AFFC_css = parse_book(AFFC_fn, AFFC_mk, names_b)
    ADWD_ch, ADWD_css = parse_book(ADWD_fn, ADWD_mk, names_b)
    book_d = {'AFFC': AFFC_ch, 'ADWD': ADWD_ch}

    # construct A Feast with Dragons
    AFWD = initialize_new_book()

    toc = []
    spine = ['nav']
    ctr = 0
    for k, v in chapter_d.items():
        ctr += 1
        ch_name = v['chapter']
        book = v['book']
        # name and roman numeral?
        name = ch_name.split(' ')[0].lower().encode()
        rest = ch_name.split(' ')[-1]
        if name in names_b and rest in roman_numerals:
            chapter_ct = rom_d[rest]
        else:
            name = ch_name.lower().encode()
            chapter_ct = 0
        new_ch_name = ch_name + ' ' + v['book']
        this_link = new_ch_name.replace(' ', '_') + '.html'
        this_chapter = epub.EpubHtml(title=new_ch_name,
                                     file_name=this_link,
                                     lang='en', uid=str(ctr))
        this_chapter.set_content(book_d[book][name][chapter_ct]['content'])
        toc.append(epub.Link(this_link, ch_name))
        spine.append(this_chapter)
        AFWD.add_item(this_chapter)

AFWD.toc = toc
AFWD.spine = spine
AFWD.add_item(AFFC_css)
AFWD.add_item(epub.EpubNav())

epub.write_epub('A Feast with Dragons.epub', AFWD)
