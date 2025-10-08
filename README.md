# 🌍 Volontariato Digitale

Una piattaforma web moderna per facilitare l'incontro tra volontari, associazioni e cittadini, tramite un sistema di matching geolocalizzato e strumenti digitali sicuri, accessibili e inclusivi.

## 🎯 Obiettivi del progetto

- Facilitare la partecipazione civica attraverso una **mappa interattiva degli eventi**.
- Permettere a cittadini, aziende e associazioni di **collaborare in modo trasparente**.
- Offrire un sistema **semplice, sicuro e mobile-friendly** per la gestione del volontariato.

## 🚀 Funzionalità MVP

- Registrazione/login per volontari e associazioni
- Dashboard utente e dashboard per associazioni
- Creazione e pubblicazione eventi
- Visualizzazione eventi su mappa (Leaflet.js) con filtri
- Candidatura degli utenti agli eventi
- Sistema di notifiche via email
- Interfaccia responsive

---

## 🧱 Struttura del progetto

```
volo/
│
├── app/
│   ├── __init__.py
│   ├── models/
│   ├── forms/
│   ├── templates/
│   ├── static/
│   ├── utils/
│   └── config.py
│
├── migrations/
├── tests/
├── .env
├── .flaskenv
├── requirements.txt
├── run.py
└── README.md
```

ℹ️ **Nota:** l'ambiente virtuale Python `venv/` è posizionato **in `projects/`**, a un livello superiore rispetto alla cartella `volo/`:

```
C:\Users\stefa\Documents\projects\venv
```

---

## 🛠️ Come installare e avviare il progetto

### 1. Creare l'ambiente virtuale (solo la prima volta)

```bash
cd C:\Users\stefa\Documents\projects
python -m venv venv
```

### 2. Attivare l'ambiente virtuale

```bash
# Su Windows
venv\Scripts\activate
```

### 3. Installare le dipendenze

```bash
cd volo
pip install -r requirements.txt
```

### 4. Avviare l'app Flask

```bash
flask run
```

oppure

```bash
python run.py
```

---

## 🔒 Sicurezza & Accessibilità

- Validazione degli input e protezione CSRF/XSS
- Conformità GDPR (uso file `.env` e sessioni sicure)
- Layout responsive e design accessibile (WCAG AA)

---

## 📍 Tecnologie utilizzate

- **Backend**: Python + Flask
- **Frontend**: HTML5, CSS3 (TailwindCSS), JavaScript
- **Database**: SQLite (MVP), PostgreSQL (produzione)
- **Mappe**: Leaflet.js
- **Tooling**: Git, Docker (opzionale), Flask-Migrate

---

## 📬 Contatti

Progetto gestito da:  
*Coordinatore tecnico*: [tuo nome]  
Email: [tua email]  
GitHub: [eventuale repo]

---

## 📄 Licenza

Questo progetto è open-source e rilasciato sotto licenza MIT.
