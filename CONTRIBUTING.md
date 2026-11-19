# Contributing / Współtworzenie

Song Generator is open source (MIT). Bug reports, ideas and pull requests are welcome.
Song Generator jest otwarty (MIT). Zgłoszenia błędów, pomysły i pull requesty są mile widziane.

## Reporting a bug / Zgłaszanie błędu

Open an issue and include / Otwórz zgłoszenie i podaj:
- Windows version, GPU and its memory / wersja Windowsa, karta graficzna i jej pamięć,
- app version (the **?** view → About) / wersja programu (widok **?** → O programie),
- what you did, what you expected, what happened / co zrobiłeś, czego oczekiwałeś, co się stało,
- the console output of `start.cmd`, if there is any error / wynik z konsoli `start.cmd`, jeśli jest błąd.

## Code / Kod

- Python 3.12, **standard library only** (`pywebview` is the single optional dependency). Please do not add
  dependencies without discussing it first. / Tylko biblioteka standardowa; nowe zależności najpierw omów.
- The UI is plain HTML/JS in `app\ui\` (no build step). / UI to czysty HTML/JS bez budowania.
- A user-visible change needs: a line in the in-app help (`view-help` in `index.html`) if it changes what the user
  can do, an English entry in `app\ui\i18n.js`, and a row in the bug and fix history in both READMEs.
  / Zmiana widoczna dla użytkownika wymaga wpisu w pomocy, angielskiego tłumaczenia w `i18n.js` i wiersza w historii
  w obu README.
- Comments in code are in English or Polish; the commit messages in English. / Komentarze po polsku lub angielsku,
  commity po angielsku.
- Test by running the app (there is no automatic test suite): switch profiles, generate a short track, check the
  monitor window and both languages. / Brak testów automatycznych: uruchom aplikację, przełącz profile, wygeneruj
  krótki utwór, sprawdź okno monitora i oba języki.

## Licence / Licencja

By contributing you agree that your contribution is licensed under the MIT licence of this project.
Wnosząc zmiany, zgadzasz się na ich licencjonowanie na licencji MIT tego projektu.
