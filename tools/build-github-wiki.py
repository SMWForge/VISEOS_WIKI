#!/usr/bin/env python3
"""Erzeugt das GitHub-Wiki (VISEOS_WIKI.wiki.git) aus den Seiten dieses Repos.

  tools/build-github-wiki.py <pfad-zum-wiki-klon>

- Seiten bekommen Wiki-Namen (Home, Überblick, Gerät-tegu, …). Das Wiki zeigt den Dateinamen
  als Titel, deshalb fällt die erste Überschrift weg.
- Links auf NN-Name.md(#anker) werden zu Wiki-Links Name(#anker).
- Die Vor/Zurück-Zeile wandert ans Seitenende, dazu kommen _Sidebar.md und _Footer.md.
- Seiten im Wiki, die hier nicht vorkommen, werden entfernt (das Wiki ist reine Ausgabe).
Danach im Wiki-Klon: git add -A && git commit && git push
"""
import os
import re
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
SRC = os.path.dirname(HERE)

PAGES = [  # (Quelle, Wiki-Seite, Titel in der Navigation)
    ('README.md', 'Home', 'Start'),
    ('01-Ueberblick.md', 'Überblick', 'Überblick'),
    ('02-Quellbaum-und-Aufbau.md', 'Quellbaum-und-Aufbau', 'Quellbaum und Aufbau'),
    ('03-Geraet-tegu.md', 'Gerät-tegu', 'Gerät tegu'),
    ('04-Blobs.md', 'Proprietäre-Blobs', 'Proprietäre Blobs'),
    ('05-System-Apps.md', 'System-Apps', 'System-Apps'),
    ('06-Werkzeuge.md', 'Werkzeuge', 'Werkzeuge'),
    ('07-OTA-Updates.md', 'OTA-Updates', 'OTA-Updates'),
    ('08-Signierung.md', 'Signierung', 'Signierung'),
    ('09-Bauen.md', 'Bauen-und-Flashen', 'Bauen und Flashen'),
    ('10-Offene-Punkte.md', 'Offene-Punkte', 'Offene Punkte'),
    ('11-Aenderungsprotokoll.md', 'Änderungsprotokoll', 'Änderungsprotokoll'),
]
NAME = {src: wiki for src, wiki, _ in PAGES}
LINK_RE = re.compile(r'\]\(([0-9A-Za-z_-]+\.md|README\.md)(#[^)]*)?\)')
NAV_RE = re.compile(r'^\[← [^\n]*\]\([^)]*\)[^\n]*\n+', re.M)


def convert(src, text):
    if src != 'README.md':
        text = re.sub(r'\A# [^\n]*\n+', '', text)            # Titel zeigt das Wiki selbst
    text = NAV_RE.sub('', text, count=1)                       # alte Vor/Zurück-Zeile
    text = LINK_RE.sub(lambda m: '](%s%s)' % (NAME[m.group(1)], m.group(2) or ''), text)
    return text.rstrip() + '\n'


def nav(i):
    parts = []
    if i > 0:
        parts.append('[← %s](%s)' % (PAGES[i - 1][2], PAGES[i - 1][1]))
    if i < len(PAGES) - 1:
        parts.append('[%s →](%s)' % (PAGES[i + 1][2], PAGES[i + 1][1]))
    return '\n---\n\n' + ' · '.join(parts) + '\n'


def main():
    if len(sys.argv) != 2 or not os.path.isdir(os.path.join(sys.argv[1], '.git')):
        sys.exit(__doc__)
    out = sys.argv[1]
    keep = {'_Sidebar.md', '_Footer.md'}
    for i, (src, wiki, _title) in enumerate(PAGES):
        text = convert(src, open(os.path.join(SRC, src), encoding='utf-8').read())
        if src != 'README.md':
            text += nav(i)
        with open(os.path.join(out, wiki + '.md'), 'w', encoding='utf-8') as f:
            f.write(text)
        keep.add(wiki + '.md')

    sidebar = ['**[ViseOS-Wiki](Home)**', '']
    for n, (_src, wiki, title) in enumerate(PAGES[1:], 1):
        sidebar.append('%d. [%s](%s)' % (n, title, wiki))
    sidebar += ['', '---', '',
                '**Schnellzugriff**', '',
                '- [App hinzufügen](Werkzeuge#vise-appsh)',
                '- [Release bauen](OTA-Updates#veröffentlichen-mit-build_and_updatesh)',
                '- [Bootloader sperren](Bauen-und-Flashen#bootloader-wieder-sperren)',
                '- [OTA-Server einrichten](OTA-Updates#der-ota-server)']
    with open(os.path.join(out, '_Sidebar.md'), 'w', encoding='utf-8') as f:
        f.write('\n'.join(sidebar) + '\n')
    with open(os.path.join(out, '_Footer.md'), 'w', encoding='utf-8') as f:
        f.write('ViseOS · SMWForge · Quelle der Seiten: Repo '
                '[VISEOS_WIKI](https://github.com/SMWForge/VISEOS_WIKI) '
                '(`tools/build-github-wiki.py`). Änderungen bitte dort machen.\n')

    for name in os.listdir(out):
        if name.endswith('.md') and name not in keep:
            os.remove(os.path.join(out, name))
            print('entfernt:', name)
    print('Wiki erzeugt: %d Seiten + _Sidebar + _Footer in %s' % (len(PAGES), out))


if __name__ == '__main__':
    main()
