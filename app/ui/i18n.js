// UI languages for Song Generator: Polish (the page's own language) and English.
// The page is written in Polish; this file swaps the visible text in place. Exact strings first, then
// patterns for text with variables. Notes, lyrics, logs and form values are the user's own words and are
// never touched. The language comes from ?lang=xx, then the choice saved by the switcher in the header,
// then the system language (anything but Polish -> English). Switching reloads the page.
// Trimmed from an earlier tool by the same author. Text without a translation stays in Polish.
(function () {
  const LANGS = { pl: 'Polski', en: 'English' };
  const saved = (() => { try { return localStorage.getItem('sg_lang'); } catch { return null; } })();
  const system = /^pl\b/i.test(navigator.language || 'pl') ? 'pl' : 'en';
  let lang = new URLSearchParams(location.search).get('lang') || saved || system;
  if (!LANGS[lang]) lang = 'pl';

  // [Polish, English]
  const T = [
    ['Modele', 'Models'],
    ['Modele i ustawienia', 'Models and settings'],
    ['sprawdzam model…', 'checking the model…'],
    ['Tekst', 'Text'],
    ['Usuń', 'Remove'],
    ['Rozmiar', 'Size'],
    ['Kroki', 'Steps'],
    ['Generuj', 'Generate'],
    ['Muzyka', 'Music'],
    ['tylko muzyka + okrzyki chórku', 'music + backing calls only'],
    ['w trybie „tylko muzyka + okrzyki” Gemma nie pisze tekstu – wpisz okrzyki sam albo wybierz głos', 'in “music + backing calls only” Gemma writes no lyrics – type the calls yourself or pick a voice'],
    ['Tytuł (nazwa pliku i listy; puste = gatunek i opis)', 'Title (file and list name; empty = genre and description)'],
    ['np. Letnia noc nad jeziorem', 'e.g. Summer night by the lake'],
    ['Wstawia znacznik w miejscu kursora w tekście', 'Inserts a tag at the cursor in the lyrics'],
    ['Szablon ▾', 'Template ▾'],
    ['Wstaw szablon: wg ustawień albo ze ściągawki (zastępuje tekst, Ctrl+Z cofa)', 'Insert a template: from the settings or the cheat sheet (replaces the text, Ctrl+Z undoes)'],
    ['Z długości, gatunku i wokalu; kolejne kliknięcie = inny układ', 'From the length, genre and voice; each click = another layout'],
    ['Utwór bez śpiewu. Wybierz', 'A song without singing. Pick'],
    ['Dopasuj mój tekst do szablonu', 'Fit my lyrics to the template'],
    ['Gemma układa Twój gotowy tekst (pole niżej) w szablon z pola wyżej – bez dopisywania własnych słów', 'Gemma lays your finished lyrics (box below) into the template above – without adding words of its own'],
    ['Twój gotowy tekst (do dopasowania)', 'Your finished lyrics (to fit in)'],
    ['Wklej tu tekst piosenki (z Claude, z notatek…), znaczniki niepotrzebne. Możesz zaznaczyć refren słowem „Refren:”. Potem „Dopasuj mój tekst do szablonu”.', 'Paste the song text here (from Claude, notes…), no tags needed. You can mark the chorus with “Chorus:”. Then “Fit my lyrics to the template”.'],
    ['wklej swój tekst w pole „Twój gotowy tekst”', 'paste your lyrics into “Your finished lyrics”'],
    ['szablon nie ma pustych miejsc – wstaw szablon albo same znaczniki', 'the template has no empty places – insert a template or just the tags'],
    ['dopasowuję tekst…', 'fitting the lyrics…'],
    ['tekst dopasowany – sprawdź i kliknij Generuj', 'lyrics fitted – check them and click Generate'],
    ['nie zmieściło się wersów:', 'lines that did not fit:'],
    ['dodatkowa zwrotka', 'an extra verse'],
    ['zostały puste miejsca – „Gemma: wypełnij tekst” je uzupełni', 'empty places left – “Gemma: fill in the lyrics” fills them'],
    ['Gemma zmieniła część słów – porównaj z oryginałem', 'Gemma changed some words – compare with your original'],
    ['Wklej najpierw swój tekst.', 'Paste your lyrics first.'],
    ['Szablon nie ma pustych miejsc (linii „...”).', 'The template has no empty places (“...” lines).'],
    ['Generuj wszystko', 'Generate all'],
    ['Generuj muzykę', 'Generate music'],
    ['Gemma pisze tekst w puste miejsca, potem powstaje muzyka', 'Gemma writes lyrics into the empty places, then the music is made'],
    ['Muzyka z tekstem z pola (albo bez śpiewu)', 'Music with the lyrics in the box (or without singing)'],
    ['tekst ≈', 'lyrics ≈'],
    ['długość ustawiona na', 'length set to'],
    ['tekst potrzebuje ok.', 'the lyrics need about'],
    ['tekst za długi na 5 min – końcówka może zostać ucięta', 'lyrics too long for 5 min – the end may be cut off'],
    ['nic do wypełnienia – tekst nie ma pustych miejsc', 'nothing to fill in – the lyrics have no empty places'],
    ['Gemma: wypełnij tekst', 'Gemma: fill in the lyrics'],
    ['Gemma wypełnia kropki szablonu (Twoje wersy zostają); bez szablonu najpierw sam go tworzy', 'Gemma fills the template’s dots (your lines stay); without a template it makes one first'],
    ['Brak szablonu do wypełnienia.', 'No template to fill in.'],
    ['Szablon', 'Template'],
    ['szablon gotowy – wpisz tekst w miejsce kropek (Ctrl+Z przywraca poprzedni tekst)', 'template ready – type your words in place of the dots (Ctrl+Z brings the old text back)'],
    ['Struktura', 'Structure'],
    ['Instrumenty', 'Instruments'],
    ['Wstawki chórku', 'Backing calls'],
    ['Szablon wg ustawień', 'Template from the settings'],
    ['Szablon ze ściągawki', 'Cheat-sheet template'],
    ['Shift + prawy przycisk = zwykłe menu', 'Shift + right click = the normal menu'],
    ['Zaznacz wszystkie', 'Select all'],
    ['Odznacz', 'Deselect'],
    ['Zaznacz', 'Select'],
    ['Usuń z historii', 'Remove from history'],
    ['Gotowe', 'Done'],
    ['Zamknij', 'Close'],
    ['Tytuł', 'Title'],
    ['Wokal', 'Vocals'],
    ['bez wokalu (podkład)', 'no vocals (backing track)'],
    ['głos kobiecy', 'female voice'],
    ['głos męski', 'male voice'],
    ['głos dziecięcy', 'child voice'],
    ['duet kobieta + mężczyzna', 'female + male duet'],
    ['chór', 'choir'],
    ['Język śpiewu', 'Singing language'],
    ['polski', 'Polish'],
    ['angielski', 'English'],
    ['włoski', 'Italian'],
    ['niemiecki', 'German'],
    ['hiszpański', 'Spanish'],
    ['francuski', 'French'],
    ['Tekst piosenki – znaczniki [Verse 1], [Chorus], [Bridge] (puste = Gemma napisze z opisu; prawy przycisk = wstaw znacznik)', 'Lyrics – tags [Verse 1], [Chorus], [Bridge] (empty = Gemma writes them from the description; right click = insert a tag)'],
    ['piszę tekst piosenki…', 'writing the lyrics…'],
    ['tekst gotowy – popraw go, jeśli chcesz, i kliknij Generuj', 'lyrics ready – edit them if you like and click Generate'],
    ['Model nie napisał tekstu piosenki - spróbuj jeszcze raz.', 'The model did not write the lyrics - try again.'],
    ['Start', 'Start'],
    ['Gatunek', 'Genre'],
    ['Skład', 'Ensemble'],
    ['(dowolny)', '(any)'],
    ['Muzyka klasyczna', 'Classical'],
    ['Filmowa / epicka', 'Cinematic / epic'],
    ['Firmowa / prezentacja', 'Corporate / presentation'],
    ['Kwartet smyczkowy', 'String quartet'],
    ['Syntezatory / elektronika', 'Synths / electronic'],
    ['Gitara i pianino', 'Guitar and piano'],
    ['Gitara akustyczna solo', 'Solo acoustic guitar'],
    ['Ukulele i perkusjonalia', 'Ukulele and percussion'],
    ['Wybierz gatunek albo opisz podkład.', 'Pick a genre or describe the track.'],
    ['Orkiestra symfoniczna', 'Symphony orchestra'],
    ['Zespół rockowy', 'Rock band'],
    ['Pianino solo', 'Solo piano'],
    ['np. spokojny podkład do filmu z gór, ciepły i optymistyczny', 'e.g. calm track for a mountain video, warm and optimistic'],
    ['Wyciszenie na końcu', 'Fade out at the end'],
    ['tłumaczę opis…', 'translating the description…'],
    ['Długość', 'Length'],
    ['1,5 min', '1.5 min'],
    ['2,5 min', '2.5 min'],
    ['Tempo (BPM)', 'Tempo (BPM)'],
    ['Puste = tempo gatunku albo dobór przez model. 70 = spokojnie, 120 = żwawo', 'Empty = the genre’s tempo or the model decides. 70 = calm, 120 = lively'],
    ['MP3 – mały plik; WAV – bez strat, kilkadziesiąt MB', 'MP3 – small file; WAV – lossless, tens of MB'],
    ['-1 = losowo; ten sam seed i opis = ten sam utwór', '-1 = random; same seed and description = same track'],
    ['tu pojawi się utwór', 'the track will appear here'],
    ['Utwory nie zapisują się same – historia znika po zamknięciu okna. „Zapisz…” pyta, gdzie zapisać plik.', 'Tracks are not saved by themselves – the history is gone when the window closes. “Save…” asks where to save the file.'],
    ['Opisz nastrój i gatunek podkładu.', 'Describe the mood and genre of the track.'],
    ['Załadowany profil nie ma modelu muzyki - załaduj profil z ACE-Step.', 'The loaded profile has no music model - load a profile with ACE-Step.'],
    ['Kobold nie zwrócił dźwięku (błąd w trakcie generowania - spróbuj krótszego utworu).', 'Kobold returned no audio (error during generation - try a shorter track).'],
    ['Zapisz…', 'Save…'],
    ['Odśwież', 'Refresh'],
    ['Zwalnia kartę graficzną; Kobold czeka w tle na następny profil', 'Frees the graphics card; Kobold waits in the background for the next profile'],
    ['Wyłącz model', 'Unload model'],
    ['Karta graficzna', 'Graphics card'],
    ['Zwykle nic tu nie trzeba klikać:', 'Usually there is nothing to click here:'],
    ['Opis', 'Description'],
    ['Temperatura', 'Temperature'],
    ['Zapisz', 'Save'],
    ['Pliki modeli', 'Model files'],
    ['Nowe modele wrzucaj do folderu modeli (pliki', 'Put new models into the models folder (files'],
    [') i kliknij Odśwież.', ') and click Refresh.'],
    ['Przetłumacz', 'Translate'],
    ['na język:', 'into:'],
    ['obraz/dźwięk (mmproj)', 'image/audio (mmproj)'],
    ['Model spoza profili', 'Model outside the profiles'],
    ['Model wyłączony', 'Model unloaded'],
    ['Kobold nie działa', 'Kobold is not running'],
    ['brak odczytu karty (nvidia-smi)', 'no reading from the card (nvidia-smi)'],
    ['domyślny', 'default'],
    ['załadowany', 'loaded'],
    ['brak pliku', 'file missing'],
    ['szacunek', 'estimate'],
    ['Przeładuj', 'Reload'],
    ['Załaduj', 'Load'],
    ['Plik', 'File'],
    ['Rodzaj', 'Type'],
    ['Kwantyzacja', 'Quantisation'],
    ['obraz', 'image'],
    ['Wyłączam model…', 'Unloading the model…'],
    ['Model właśnie odpowiada – nic nie podmieniłem. Spróbuj za chwilę.', 'The model is answering right now – nothing was swapped. Try again in a moment.'],
    ['Nie udało się załadować – szczegóły w logu powyżej.', 'Loading failed – details in the log above.'],
    ['Język', 'Language'],
    ['mowa → tekst', 'speech → text'],
    ['tekst', 'text'],
    ['angielski', 'English'],
    ['model wyłączony (Kobold czeka na profil)', 'model unloaded (Kobold is waiting for a profile)'],
    ['Pusty tekst do tłumaczenia.', 'Nothing to translate.'],
    ['Tekst za długi do tłumaczenia (limit 20 000 znaków).', 'Text too long to translate (limit 20,000 characters).'],
    ['Załadowany profil nie ma modelu tekstowego - załaduj np. profil gemma.', 'The loaded profile has no text model - load e.g. the gemma profile.'],
    ['Model nie zwrócił tłumaczenia.', 'The model returned no translation.'],
    ['Nie ma takiego profilu.', 'No such profile.'],
    ['To profil domyślny - najpierw ustaw inny jako domyślny.', 'This is the default profile - set another one as default first.'],
    ['Ten profil jest teraz załadowany - najpierw załaduj inny.', 'This profile is loaded right now - load another one first.'],
    ['Nieznane zadanie.', 'Unknown task.'],
    ['Kobold nie działa.', 'Kobold is not running.'],
    ['Kobold bez trybu admin - zamknij jego okno ręcznie.', 'Kobold is not in admin mode - close its window by hand.'],
    ['Model właśnie generuje - spróbuj za chwilę.', 'The model is generating right now - try again in a moment.'],
    ['Kobold odrzucił polecenie.', 'Kobold refused the command.'],
    ['Kobold nie potwierdził wyłączenia w 60 s - sprawdź stan za chwilę.', 'Kobold did not confirm unloading within 60 s - check again in a moment.'],
    ['Nazwa profilu: małe litery, cyfry i _, do 32 znaków.', 'Profile name: lowercase letters, digits and _, up to 32 characters.'],
    ['Plik', 'File'],
    ['folder', 'folder'],
    ['co', 'every'],
    ['Zamknij', 'Close'],
    // ---- Song Generator additions
    ['Załadowany profil', 'Loaded profile'],
    ['Ładuję…', 'Loading…'],
    ['model wyłączony – załaduje się sam przy następnym zadaniu', 'model unloaded – it loads by itself at the next task'],
    ['model niedostępny – uruchom serwer (KoboldCpp)', 'model unavailable – start the server (KoboldCpp)'],
    ['brak połączenia z serwerem aplikacji', 'no connection to the app server'],
    ['brak połączenia z aplikacją', 'no connection to the app'],
    ['brak odczytu (nvidia-smi)', 'no reading (nvidia-smi)'],
    ['(dłużej niż zwykle)', '(longer than usual)'],
    ['Nie udało się pobrać listy modeli.', 'Could not fetch the list of models.'],
    ['Model wyłączony – karta graficzna wolna. Załaduje się sam przy następnym zadaniu.', 'Model unloaded – the graphics card is free. It loads by itself at the next task.'],
    ['Błąd:', 'Error:'],
    ['błąd', 'error'],
    ['Tytuł: …', 'Title: …'],
    ['Modele przełączają się same: Gemma pisze tekst, ACE-Step robi muzykę.', 'Models switch by themselves: Gemma writes the lyrics, ACE-Step makes the music.'],
    ['Opis stylu – nastrój, do czego (opcjonalnie)', 'Style description – mood, what it is for (optional)'],
    ['na górnym pasku, żeby pisać tekst, wstawić szablon albo dopasować własny tekst.', 'in the top bar to write lyrics, insert a template or fit your own lyrics.'],
    ['Zapisz wszystkie', 'Save all'],
    ['Utwory nie zapisują się same – historia znika po zamknięciu okna. „Zapisz…” pyta, gdzie zapisać plik. Model: ACE-Step 1.5 (licencja MIT; autorzy dopuszczają użycie komercyjne, np. na YouTube). Przy wgrywaniu na YouTube zaznacz, że treść powstała z pomocą AI, i nie proś o naśladowanie konkretnego wykonawcy. Wokal: tekst śpiewa model muzyki, rodzaj głosu idzie do opisu stylu – model zwykle go słucha, ale nie zawsze.', 'Tracks are not saved by themselves – the history disappears when the window is closed. “Save…” asks where to save the file. Model: ACE-Step 1.5 (MIT licence; the authors allow commercial use, e.g. on YouTube). When uploading to YouTube, state that the content was made with the help of AI, and do not ask for the imitation of a specific artist. Vocals: the music model sings the lyrics, the kind of voice goes into the style description – the model usually follows it, but not always.'],
    ['Profile (jeden profil = jeden zestaw modeli w pamięci karty)', 'Profiles (one profile = one set of models in the card’s memory)'],
    ['„Generuj” samo ładuje potrzebny profil (', '“Generate” loads the profile it needs by itself ('],
    ['– teksty,', '– lyrics,'],
    ['– ACE-Step). Oba naraz nie mieszczą się w pamięci karty, więc zawsze działa jeden; przełączenie trwa 15–60 s. Jeśli model akurat generuje, przełączenie się nie uda – spróbuj za chwilę. Zestawy plików zmieniasz w', '– ACE-Step). Both do not fit in the card’s memory at once, so only one runs at a time; switching takes 15–60 s. If the model is generating at that moment, the switch will fail – try again in a moment. You change the file sets in'],
    ['Podgląd: GPU, CPU, RAM (małe okienko)', 'Monitor: GPU, CPU, RAM (small window)'],
    ['Kroki dyfuzji 4–50: więcej = dokładniej, ale wolniej. Domyślnie 8', 'Diffusion steps 4–50: more = more accurate but slower. Default 8'],
    ['[verse] Idę przez miasto o świcie ... [chorus] ...', '[verse] I walk through the city at dawn ... [chorus] ...'],
    ['zły JSON albo plik za duży', 'bad JSON or file too large'],
    ['Model nie dopasował tekstu - spróbuj jeszcze raz.', 'The model did not fit the lyrics – try again.'],
    ['Model muzyki nie ułożył planu utworu:', 'The music model did not make a plan for the track:'],
    ['Nazwy istniejącego profilu nie zmieniamy.', 'An existing profile cannot be renamed.'],
    ['Tekst i muzyka nie mieszczą się razem w pamięci karty — to dwa osobne profile.', 'Text and music do not fit together in the card’s memory – they are two separate profiles.'],
    ['Muzyka (ACE-Step) potrzebuje czterech plików: LM, embeddings, DiT i VAE.', 'Music (ACE-Step) needs four files: LM, embeddings, DiT and VAE.'],
    ['Gemma 4 12B - pisze teksty piosenek, dopasowuje Twój tekst do szablonu, proponuje tytuł', 'Gemma 4 12B – writes song lyrics, fits your lyrics to the template, suggests a title'],
    ['ACE-Step 1.5 - utwory do 5 min (MIT, użytek komercyjny dozwolony)', 'ACE-Step 1.5 – tracks up to 5 min (MIT, commercial use allowed)'],
    ['Uruchamiam profil...', 'Starting the profile...'],
    ['Model jest zajęty (trwa generowanie albo kolejka) - nic nie podmieniam. Spróbuj później.', 'The model is busy (generating or queued) – I am not switching anything. Try later.'],
    ['Model zajął się generowaniem - nic nie podmieniam. Spróbuj później.', 'The model started generating – I am not switching anything. Try later.'],
    ['KoboldCpp odrzucił podmianę (plik spoza admin_dir?).', 'KoboldCpp refused the switch (file outside admin_dir?).'],
    ['Model nie wstał w zadanym czasie (wait_s w serwer.json).', 'The model did not come up in time (wait_s in serwer.json).'],
    ['Podgląd', 'Monitor'],
    ['użycie', 'usage'],
    ['pobór', 'power'],
    ['Wentylatory', 'Fans'],
    ['Temperatura CPU: uruchom HWiNFO z włączonym „Shared Memory Support”.', 'CPU temperature: run HWiNFO with “Shared Memory Support” enabled.'],
  ];
  // Patterns for text with variables: [regex, English with $1 $2 ...]
  const P = [
    [/^ładuję profil (.+)…$/, 'loading profile $1…'],
    [/^przełączam na profil „(.+)” \(ok\. 15–40 s\)…$/, 'switching to profile "$1" (about 15–40 s)…'],
    [/^Nie udało się załadować „(.+)”: (.*)$/s, 'Could not load "$1": $2'],
    [/^gotowe w (.+) s$/, 'done in $1 s'],
    [/^Zapisz zaznaczone \((\d+)\)$/, 'Save selected ($1)'],
    [/^Zapisz wszystkie \((\d+)\)$/, 'Save all ($1)'],
    [/^zapisuję (\d+) z (\d+)…$/, 'saving $1 of $2…'],
    [/^zapisano plików: (\d+)( → .*)?$/, 'files saved: $1$2'],
    [/^komponuję… (\d+) s$/, 'composing… $1 s'],
    [/^Model muzyki nie ułożył planu utworu: (.+)$/, 'The music model could not plan the track: $1'],
    [/^gotowe w (.+) s · (.+)$/, 'done in $1 s · $2'],
    [/^Błąd: (.*)$/s, 'Error: $1'],
    [/^(.*)\nBłąd: (.*)$/s, '$1\nError: $2'],
    [/^Profil: (.*)$/, 'Profile: $1'],
    [/^zajęte (.+) z (.+)$/, '$1 of $2 in use'],
    [/^~(.+) · część w RAM$/, '~$1 · partly in RAM'],
    [/^Ładuję (.+)…$/, 'Loading $1…'],
    [/^Załadowano profil (.+)\.$/, 'Profile $1 loaded.'],
    [/^(.*) · pracuje$/, '$1 · working'],
    [/^Profil '(.+)' już istnieje - wybierz inną nazwę\.$/, 'Profile \'$1\' already exists - choose another name.'],
    [/^Trwa już ładowanie '(.+)'\.$/, '\'$1\' is already loading.'],
    [/^Zła wartość: (.+)$/, 'Invalid value: $1'],
    [/^(.+) poza zakresem (.+)$/, '$1 out of range $2'],
    // ---- Song Generator additions
    [/^Czekam na wczytanie modelu(\.*) gotowe\.$/, 'Waiting for the model to load$1 done.'],
    [/^Czekam na wczytanie modelu(\.*)$/, 'Waiting for the model to load$1'],
    [/^Podmieniam model na '(.+)' \(admin API KoboldCpp\)\.$/, 'Switching the model to \'$1\' (KoboldCpp admin API).'],
    [/^Uruchamiam profil '(.+)'\.\.\.$/, 'Starting profile \'$1\'...'],
    [/^Model już działa: (.+)$/, 'The model is already running: $1'],
    [/^Brak pliku modelu '(.+)': (.+)$/, 'Missing model file \'$1\': $2'],
    [/^Proces modelu zakończył się \(kod (\d+)\) - sprawdź parametry profilu\.$/, 'The model process ended (code $1) – check the profile parameters.'],
    [/^Kobold działa bez trybu admin .*$/, 'Kobold runs without admin mode (started by hand) – the model cannot be switched without closing it. Close the Kobold window and start again.'],
    [/^Załaduj profil (.+)$/, 'Load profile $1'],
    [/^Ładuję (.+)…$/, 'Loading $1…'],
    [/^Załadowano profil (.+)\.$/, 'Profile $1 loaded.'],
    [/^ładuję profil (.+)… (\d+)% · (\d+) s \(dłużej niż zwykle\)$/, 'loading profile $1… $2% · $3 s (longer than usual)'],
    [/^ładuję profil (.+)… (\d+)% · (\d+) s$/, 'loading profile $1… $2% · $3 s'],
    [/^komponuję… (\d+) s$/, 'composing… $1 s'],
    [/^· ~(.+) z (.+) \(część w RAM\)$/, '· ~$1 of $2 (partly in RAM)'],
    [/^· ~(.+) z (.+)$/, '· ~$1 of $2'],
    [/^(~.+) · część w RAM$/, '$1 · partly in RAM'],
    [/^Błąd generowania muzyki: (.+)$/, 'Error generating music: $1'],
    [/^Błąd dopasowania tekstu: (.+)$/, 'Error fitting the lyrics: $1'],
    [/^Błąd pisania tekstu: (.+)$/, 'Error writing the lyrics: $1'],
    [/^Błąd tłumaczenia: (.+)$/, 'Error translating: $1'],
    [/^Błąd (.+): (.+)$/, 'Error $1: $2'],
    [/^Żaden profil nie ma (.+) - dodaj go w panelu Modele\.$/, 'No profile has $1 – add it in the Models panel.'],
  ];

  const col = lang === 'en' ? 1 : 0;
  const norm = s => s.replace(/\s+/g, ' ').trim();
  const EXACT = new Map(col ? T.map(r => [norm(r[0]), r[1]]) : []);
  // One text -> translation or undefined. Parts captured by a pattern are translated too
  // ("Błąd: " + a server message), a few levels deep; status marks (✓ ✗ ⚠ ✉) are kept in front.
  function core(key, depth) {
    let out = EXACT.get(key);
    if (out !== undefined) return out;
    const mark = key.match(/^([✓✗⚠✉]️?\s+)(.+)$/s);
    if (mark) { const r = core(mark[2], depth); return r === undefined ? undefined : mark[1] + r; }
    for (const p of P) {
      const m = key.match(p[0]);
      if (!m) continue;
      return p[col].replace(/\$(\d)/g, (_, n) => {
        const part = m[n] || '';
        const t = depth < 3 && part ? core(part, depth + 1) : undefined;
        return t === undefined ? part : t;
      });
    }
    return undefined;
  }
  function tr(s) {
    if (!col || !s) return s;
    const key = norm(s);
    if (!key) return s;
    const out = core(key, 0);
    if (out === undefined) return s;
    return s.match(/^\s*/)[0] + out + s.match(/\s*$/)[0];  // keep the surrounding whitespace
  }
  // The user's and the model's words are never translated.
  const SKIP = '.log, script, style, code, .files td:first-child';
  function walk(root) {
    if (!col || !root) return;
    if (root.nodeType === 3) {
      if (!root.parentElement?.closest(SKIP + ', textarea')) { const t = tr(root.data); if (t !== root.data) root.data = t; }
      return;
    }
    if (root.nodeType !== 1 || root.closest(SKIP)) return;
    for (const a of ['title', 'placeholder']) {
      const v = root.getAttribute(a);
      if (v) { const t = tr(v); if (t !== v) root.setAttribute(a, t); }
    }
    for (const c of root.childNodes) walk(c);
  }
  window.I18N = { lang, LANGS, tr, walk };
  if (!col) return;
  document.documentElement.lang = lang;
  const start = () => {
    walk(document.body);
    new MutationObserver(list => {
      for (const m of list) {
        if (m.type === 'childList') m.addedNodes.forEach(walk);
        else if (m.type === 'characterData') walk(m.target);
        else walk(m.target);
      }
    }).observe(document.body, { subtree: true, childList: true, characterData: true,
                               attributes: true, attributeFilter: ['title', 'placeholder'] });
  };
  if (document.body) start(); else document.addEventListener('DOMContentLoaded', start);
})();
