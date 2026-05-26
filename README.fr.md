<p align="center">
  <img src="docs/logo.png" alt="DeepRenPyTrans Logo" width="250">
</p>

# 🎮 DeepRenPyTrans

**Traducteur universel pour visual novels Ren'Py propulsé par l'IA.**

🌐 [English](README.md) | [Русский](README.ru.md) | [Español](README.es.md) | [Português](README.pt.md) | [Deutsch](README.de.md) | [Français](README.fr.md) | [简体中文](README.zh.md)

---

Traduisez n'importe quel jeu Ren'Py vers n'importe quelle langue en utilisant DeepSeek (y compris `deepseek-v4-flash` / `deepseek-v4-pro`), OpenAI ou des modèles d'IA locaux (LLM) — sans modifier le code source du jeu.

---

## ✨ Fonctionnalités

- **🔍 Extraction intelligente** — Trouve automatiquement toutes les chaînes traduisibles dans les fichiers `.rpy`, en filtrant le code, les identifiants et les messages de débogage.
- **🤖 Traduction par IA** — Traduction par lots via DeepSeek, OpenAI ou Ollama local avec prise en compte du contexte de la scène ou du chapitre.
- **🔌 Injection en temps réel** — Système de crochets (hooks) avec zéro modification des fichiers originaux du jeu, utilisant la fonction native de Ren'Py `config.replace_text`.
- **📊 Audit de qualité** — Trouve les chaînes non traduites, les traductions orphelines et les entrées inutiles (junk).
- **🧹 Nettoyage de dictionnaire** — Supprime automatiquement les chaînes de débogage, les docstrings et les artefacts de code.
- **⚡ Incrémental** — Reprend les traductions interrompues en traitant uniquement les chaînes nouvelles ou manquantes.
- **📱 Multiplateforme** — Fonctionne avec les versions PC, Android (injection dans l'APK) et iOS.

## 🚀 Démarrage Rapide

### 1. Installation

```bash
git clone https://github.com/Danko-Novak/DeepRenPyTrans.git
cd DeepRenPyTrans

# Option A : Installer comme un package (recommandé — fournit la commande `deeprenpytrans` globale)
pip install -e .

# Option B : Installer uniquement les dépendances
pip install -r requirements.txt
```

> Après avoir fait `pip install -e .`, vous pouvez utiliser directement `deeprenpytrans` au lieu de `python -m deeprenpytrans`.

### 2. Configuration

```bash
# Copier les fichiers de configuration d'exemple
cp .env.example .env
cp config.example.yaml config.yaml

# Modifiez .env avec votre clé API
# Modifiez config.yaml avec le chemin de votre jeu et la langue cible
```

Vous pouvez lancer l'outil de deux manières :

#### Option A : Interface Graphique Web (Recommandé)
Vous pouvez démarrer la console de trois manières :
- Sous Windows : Double-cliquez sur le fichier `run_gui.bat` dans le dossier racine du projet.
- Sous Linux/macOS : Exécutez le script shell :
  ```bash
  ./run_gui.sh
  ```
- Ou exécutez-le manuellement dans votre terminal :
  ```bash
  python3 gui_server.py
  ```
Cela ouvrira automatiquement votre navigateur à l'adresse `http://localhost:8000`.

#### Option B : Interface en ligne de commande (CLI)
```bash
# Étape 1 : Extraire les chaînes de votre jeu
python -m deeprenpytrans extract --game "./MonJeu/game"

# Étape 2 : Traduire avec l'IA
python -m deeprenpytrans translate --strings strings_by_file.json --dict "./MonJeu/game/tl/french/dictionary.json"

# Étape 3 : Générer les hooks de temps de exécution
python -m deeprenpytrans inject --game "./MonJeu/game" --lang french
```


## 📖 Commandes

### `extract` — Trouver les chaînes traduisibles

```bash
python -m deeprenpytrans extract --game ./MonJeu/game --output strings.json
```

Parcourt tous les fichiers `.rpy`, extrait les chaînes entre guillemets et applique des filtres intelligents pour ignorer :
- Les identifiants internes (`ITM_Sword`, `LOC_Bridge`, `ACT_NPC01`)
- Le code Python et les assertions
- Les chemins de fichiers et les codes couleur hexadécimaux
- Les messages de débogage et de log
- Les textes déjà traduits (détection des caractères de la langue cible)

Options :
| Option | Description |
|------|-------------|
| `--game PATH` | Chemin vers le répertoire `game/` du jeu |
| `--output FILE` | Fichier JSON de sortie (par défaut : `strings_by_file.json`) |
| `--include-log PATH` | Fusionner avec les chaînes non traduites de `untranslated.log` |

### `translate` — Traduction par IA

```bash
python -m deeprenpytrans translate --strings strings.json --dict dictionary.json
```

Envoie les chaînes à l'API d'IA en lots intelligents (groupés par fichier source pour conserver le contexte).
Prend en charge la traduction incrémentale — les chaînes déjà traduites sont ignorées.

### `audit` — Contrôle qualité

```bash
python -m deeprenpytrans audit --dict dictionary.json --strings strings.json
```

Génère un rapport montrant :
- ❌ Les chaînes non traduites (présentes dans le code mais pas dans le dictionnaire)
- 👻 Les traductions orphelines (présentes dans le dictionnaire mais plus dans le code)
- 🔁 Les clés et valeurs identiques (peut-être oubliées dans la traduction)
- 📭 Les traductions vides
- 🗑️ Les entrées inutiles (messages de débogage, morceaux de code)

### `clean` — Nettoyer le dictionnaire

```bash
python -m deeprenpytrans clean --dict dictionary.json --dry-run
python -m deeprenpytrans clean --dict dictionary.json --remove-orphaned
```

Options :
| Option | Description |
|------|-------------|
| `--dry-run` | Prévisualiser ce qui serait supprimé |
| `--keep-junk` | Ne pas supprimer les chaînes de débogage/code |
| `--remove-orphaned` | Supprimer également les traductions qui n'existent plus dans le code |

### `inject` — Générer hooks.rpy

```bash
python -m deeprenpytrans inject --game ./MonJeu/game --lang french
```

Génère un fichier `hooks.rpy` qui :
- Charge le fichier `dictionary.json` au démarrage du jeu.
- Intercepte tout le texte affiché via `config.replace_text`.
- Enregistre les chaînes non traduites dans `untranslated.log` en temps réel pendant que vous jouez.
- Ajoute un raccourci clavier pour activer/désactiver la traduction en direct.
- Remplace les polices d'origine par des typographies compatibles avec la langue cible.

## ⚙️ Configuration

### `config.yaml`

```yaml
game_dir: "./MonJeu/game"
target_language: "French"
translation_dir: "french"

api:
  provider: "deepseek"    # ou "openai", "openrouter", "groq", "nebius", "deepinfra", "gemini", "dashscope", "ollama"
  model: "deepseek-chat"  # prend en charge les nouveaux modèles deepseek-v4-flash / deepseek-v4-pro
  temperature: 0.2
  batch_size: 40

fonts:
  default: "DejaVuSans.ttf"
  replacements:
    "OriginalFont.ttf": "DejaVuSans.ttf"

extraction:
  skip_prefixes: ["ITM", "ACT", "LOC", "QST"]
  force_include: ["Q.Save", "Q.Load"]
```

### `.env`

```bash
DEEPSEEK_API_KEY=sk-votre-cle-ici
# ou
OPENAI_API_KEY=sk-votre-cle-openai-ici
```

> [!NOTE]
> Le support pour les modèles locaux (Ollama) et les fournisseurs d'API alternatifs (OpenAI, OpenRouter, Groq, Nebius, DeepInfra, Gemini, DashScope) autres que DeepSeek est actuellement nominal. L'outil a été optimisé à l'origine pour DeepSeek, et les autres intégrations ont été implémentées selon les normes de l'API OpenAI officielle sans tests exhaustifs. La liste des fournisseurs et des clés entièrement vérifiés sera élargie lors des prochaines mises à jour.


## 🏗️ Comment ça marche

```
┌────────────────┐     ┌──────────────┐     ┌────────────────┐
│ Fichiers .rpy  │────▶│  Extracteur  │────▶│  strings.json  │
│ (code du jeu)  │     │   (filtres)  │     │ (par fichiers) │
└────────────────┘     └──────────────┘     └───────┬────────┘
                                                    │
                                                    ▼
┌────────────────┐     ┌──────────────┐     ┌────────────────┐
│  Dictionnaire  │◀────│Traducteur IA │◀────│ Fournisseur API│
│     .json      │     │    (lots)    │     │ (DeepSeek/etc) │
└───────┬────────┘     └──────────────┘     └────────────────┘
        │
        ▼
┌────────────────┐     ┌──────────────┐
│   hooks.rpy    │────▶│  Jeu Ren'Py  │ ← Le joueur voit le texte traduit !
│  (exécution)   │     │ (exécution)  │
└────────────────┘     └──────────────┘
```

## 📱 Déploiement Mobile

### Android (Injection APK)
1. Utilisez notre script de build automatisé (`build_apk.bat` pour Windows, ou `android/build_apk.sh` pour Linux/macOS) qui gère tout le processus :
   - Extrait les ressources du jeu de l'ancien APK.
   - Restaure les ressources déjà compressées de l'APK d'origine pour économiser jusqu'à 60 % de la taille totale (économie moyenne de ~400-500 Mo).
   - Effectue la compression audio wav en ogg.
   - Optimise les nouvelles images pour mobiles tout en ignorant les ressources déjà compressées.
   - Compresse l'APK en utilisant la compression ultra et le signe automatiquement.
2. **Personnalisation** : Vous pouvez personnaliser le processus de build en modifiant les variables (flags) situées en haut du script de build (`build_apk.bat` ou `android/build_apk.sh`) :
   - `RESTORE_OLD_ASSETS` (1/0) : Activer/Désactiver la restauration des ressources déjà compressées de l'ancien APK.
   - `COMPRESS_AUDIO` (1/0) : Activer/Désactiver la conversion de wav en ogg et la mise à jour des scripts.
   - `COMPRESS_IMAGES` (1/0) : Activer/Désactiver la compression des nouvelles images.
   - `INJECT_TRANSLATION` (1/0) : Activer/Désactiver l'injection de traduction. Mettre à `0` pour générer un port propre non traduit (en langue originale).
   - `LANG_FOLDER` : Nom du dossier de langue cible dans `game/tl/` (par exemple, `french`).
   - `COMPRESSION_LEVEL` (0-9) : Niveau de compression de 7-Zip (9 = compression maximale, 0 = sans compression).
3. Si vous procédez manuellement : décompressez l'APK avec 7zip, remplacez les fichiers dans `assets/x-game/game/`, supprimez les signatures dans `META-INF/` et recompressez/signez l'APK.

### iOS
1. Générez le projet Xcode depuis le lanceur Ren'Py.
2. Ajoutez le dossier de traduction `tl/french/` au projet.
3. Compilez et déployez sur l'appareil.

## ⚠️ Note Importante et Limitations

- **Statut des Tests** : Cet outil a été testé et vérifié sur un seul jeu jusqu'à présent, où tout a été traduit et compilé correctement.
- **Code Spécifique au Jeu** : Bien que l'objectif soit de créer un outil de traduction universel parfait, d'autres jeux Ren'Py peuvent (et vont probablement) nécessiter des ajustements pour s'adapter à leur base de code spécifique, leurs préfixes personnalisés ou leurs particularités de script.
- **Pas de compétences en programmation ?** : Si vous ne savez pas programmer ou n'avez pas le temps de modifier les scripts, nous vous recommandons vivement d'utiliser des assistants de codage IA comme **Antigravity**, **Cursor** ou des outils similaires pour vous aider à adapter l'extracteur et les filtres à votre jeu cible.

## 🤝 Contribution

Les contributions sont les bienvenues ! Domaines qui ont besoin d'aide :
- Intégration de fournisseurs de LLM supplémentaires.
- Prise en charge et tests pour les langues CJK (chinois, japonais, coréen).
- Amélioration des heuristiques d'extraction pour certains jeux spécifiques.

## 🗺️ Feuille de Route et Fonctionnalités

Nous suivons notre développement, planifions de nouvelles fonctionnalités et priorisons les tâches en fonction des retours de la communauté. Si vous avez une idée ou souhaitez demander une fonctionnalité, rendez-vous dans l'onglet **Discussions** sur GitHub, soumettez votre proposition ou votez pour les idées existantes !

| Fonctionnalité | Votes | Statut | Progression |
| :--- | :--- | :--- | :--- |
| **Console Web GUI (Tableau de Bord)** | - | 🚀 Publié | `[████████████████████]` 100% |
| **Optimisateur et Assembleur d'APK** | - | 🚀 Publié | `[████████████████████]` 100% |
| **Prise en Charge des LLM Locaux et d'Ollama** | - | 🚀 Publié | `[████████████████████]` 100% |
| **Prise en Charge de macOS et Linux** | - | 🚀 Publié | `[████████████████████]` 100% |
| **Audits de Traduction Japonaise/Chinoise** | 0 | 📋 Planifié | `[█░░░░░░░░░░░░░░░░░░░]` 5% |

---

## 💖 Soutenir le Projet

DeepRenPyTrans est un projet passionné conçu pour simplifier le processus de traduction de visual novels. Si cet outil vous a fait gagner du temps ou vous a aidé à proposer un jeu à un nouveau public, pensez à soutenir son développement.

J'utilise actuellement une station de développement d'entrée de gamme et je souhaite la faire évoluer vers une station de travail dédiée à l'IA locale sous Linux avec ROCm. Cela permettra d'effectuer des tests natifs à haute vitesse des LLM locaux.

**Cagnotte Actuelle :** 0 / 1 200 USD

### 🚀 Paliers d'Évolution :
* **Palier 1 : Mise à niveau du GPU ($850)** — Achat d'un GPU AMD Radeon de 24 Go (par exemple, RX 7900 XTX ou équivalent de nouvelle génération) pour exécuter localement des modèles LLM volumineux (tels que 14B/32B/70B) sous Linux ROCm.
* **Palier 2 : Mise à niveau du stockage ($150)** — Passage à un SSD NVMe PCIe 4.0 rapide de 2 To. Les modèles LLM locaux nécessitent un espace disque important (de 5 Go à plus de 40 Go par modèle), et mon SSD actuel de 500 Go est saturé.
* **Palier 3 : Mise à niveau de la RAM ($150)** — Ajout de 32 Go de RAM supplémentaires (pour atteindre 64 Go au total) pour permettre des flux de travail parallèles, un multitâche intensif sur l'IDE et la décharge de modèles sur le processeur.
* **Dépenses courantes : Budget API ($50)** — Petit budget pour tester les API payantes (DeepSeek, OpenAI, Claude) lors de la validation des traductions.

### Comment aider :
* **Ajouter une étoile au dépôt (Star) :** Cela aide à la visibilité et me motive à continuer de coder !
* **Contribuer :** Signalez des bugs, proposez des fonctionnalités ou soumettez des PR.
* **Faire un don (USDT - TON / Réseau TON) :**
  `UQBdHUyR8nG5p_Rwhw_Rtmgc7QJdJ-G5nOPJa7Pq0mh2A27K`

## 📄 Licence

GNU AGPL v3 — voir le fichier [LICENSE](LICENSE) pour plus de détails.
