from ebooklib import epub
import csv


identifier = '23skidoo'

num_d = {1: 'I', 2: 'II', 3: 'III', 4: 'IV', 5: 'V', 6: 'VI', 7: 'VII',
         8: 'VIII', 9: 'IX', 10: 'X', 11: 'XI', 12: 'XII', 13: 'XIII'}

rom_d = {}
for k, v in num_d.items():
    rom_d[v] = k

roman_numerals = list(num_d.values())

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
    new_book.set_identifier(identifier)
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
        if i > 0:
            j = ss[i:].find(post)
            title = ss[i+delta:i+j].lower().replace(b'\xe2\x80\x99', b"'")
            if title in names:
                if name_count[title] == 0:
                    chapters[title] = {}
                name_count[title] += 1
                this_count = name_count[title]
            else:
                chapters[title] = {}
                this_count = 0
            chapters[title][this_count] = {}
            chapters[title][this_count]['name'] = item.get_name()
            content = b'<html>' + item.get_body_content() + b'</html>'
            chapters[title][this_count]['content'] = content

    css = book.get_item_with_id('css')
    ncx = book.get_item_with_id('ncx')

    return chapters, css, ncx


# NOTE ncx not working
def make_ncx_xml(book):
    with open('ncx_template.xml') as f:
        ncx_temp_l = f.readlines()
    ncx_temp_s = ''.join(ncx_temp_l).replace('[UUID]', identifier)
    ncx_body_s = '<navMap>'
    for i, c in enumerate(book.toc):
        j = i+1
        s0 = '<navPoint id="navpoint{0}" playOrder="{1}">'.format(j, j)
        s1 = '<navLabel><text>{0}</text></navLabel>'.format(c.title)
        s2 = '<content src="text/{0}"/></navPoint>'.format(c.href.replace('html', 'xhtml'))
        ncx_body_s += s0 + s1 + s2
    ncx_body_s += '</navMap>'
    return ncx_temp_s + ncx_body_s


if __name__ == "__main__":
            
    AFFC_fn = 'ASOIAF_4_A_Feast_for_Crows.epub'
    AFFC_mk = b'<h3 class="calibre5">', b'</h3>'
    ADWD_fn = 'ASOIAF_5_A_Dance_with_Dragons.epub'
    ADWD_mk = b'<span class="calibre18">', b'</span>'

    chapter_d, names_s = parse_chapters()
    names_b = [n.encode() for n in names_s]
    AFFC_ch, AFFC_css, AFFC_ncx = parse_book(AFFC_fn, AFFC_mk, names_b)
    ADWD_ch, ADWD_css, AFFC_ncx = parse_book(ADWD_fn, ADWD_mk, names_b)
    book_d = {'AFFC': AFFC_ch, 'ADWD': ADWD_ch}

    AFWD = initialize_new_book()

    toc = []
    spine = ['nav']
    ctr = 0
    for k, v in chapter_d.items():
        ctr += 1
        ch_name = v['chapter']
        book = v['book']
        name = ch_name.split(' ')[0].lower().encode()
        rest = ch_name.split(' ')[-1]
        if name in names_b and rest in roman_numerals:
            chapter_ct = rom_d[rest]
        else:
            name = ch_name.lower().encode()
            chapter_ct = 0
        #this_link = book_d[book][name][chapter_ct]['name']
        new_ch_name = ch_name + ' ' + v['book']
        this_link = new_ch_name.replace(' ', '_') + '.html'
        this_chapter = epub.EpubHtml(title=new_ch_name,
                                     file_name=this_link,
                                     lang='en', uid=identifier) # str(ctr)? identifier?
        #this_chapter = book_d[book][name][chapter_ct]['content']
        this_chapter.set_content(book_d[book][name][chapter_ct]['content'])
        toc.append(epub.Link(this_link, ch_name))
        spine.append(this_chapter)
        AFWD.add_item(this_chapter)

AFWD.toc = toc
AFWD.spine = spine
AFWD.add_item(AFFC_css)

#ncx_content = make_ncx_xml(AFWD).encode()
#AFWD_ncx = epub.EpubNcx()
#AFWD_ncx.set_content(ncx_content)
#AFWD.add_item(AFWD_ncx)

# nav not working
AFWD.add_item(epub.EpubNav())

epub.write_epub('A Feast with Dragons.epub', AFWD) #,
                #{'play_order': {'enabled': True, 'start_from': 1}})
