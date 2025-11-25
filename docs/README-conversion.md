# Conversion des PDFs en Markdown

Ce guide vous aide à convertir les fichiers PDF du dossier `docs` en fichiers Markdown.

## Fichiers PDF à convertir

- `aide-tp.pdf` → `aide-tp.md`
- `projet.pdf` → `projet.md`
- `tutoriel-bdw-server.pdf` → `tutoriel-bdw-server.md`

## Méthode 1 : Utilisation du script bash (Recommandée pour WSL)

1. Ouvrez un terminal WSL (Ubuntu)
2. Naviguez vers le dossier du projet :
```bash
cd /home/fneuf/projects/docs
```

3. Rendez le script exécutable :
```bash
chmod +x convert-pdfs-to-md.sh
```

4. Exécutez le script :
```bash
./convert-pdfs-to-md.sh
```

Le script va automatiquement :
- Vérifier et installer les outils nécessaires (poppler-utils, pandoc)
- Convertir chaque PDF en Markdown
- Ajouter un en-tête à chaque fichier
- Afficher un aperçu du résultat

## Méthode 2 : Utilisation du script PowerShell

1. Ouvrez PowerShell en tant qu'administrateur
2. Naviguez vers le dossier du projet
3. Exécutez le script :
```powershell
.\convert-pdfs-to-md.ps1
```

**Note :** Si vous obtenez une erreur d'exécution de politique, exécutez d'abord :
```powershell
Set-ExecutionPolicy -ExecutionPolicy RemoteSigned -Scope CurrentUser
```

## Méthode 3 : Conversion manuelle (commandes individuelles)

### Installation des outils (si nécessaire) :
```bash
sudo apt update
sudo apt install -y poppler-utils pandoc
```

### Conversion de chaque fichier :

```bash
cd /home/fneuf/projects/docs

# Convertir aide-tp.pdf
pdftotext aide-tp.pdf - | pandoc -f plain -t markdown -o aide-tp.md

# Convertir projet.pdf
pdftotext projet.pdf - | pandoc -f plain -t markdown -o projet.md

# Convertir tutoriel-bdw-server.pdf
pdftotext tutoriel-bdw-server.pdf - | pandoc -f plain -t markdown -o tutoriel-bdw-server.md
```

## Méthode 4 : Conversion avec OCR (si les PDFs sont des images scannées)

Si les PDFs contiennent des images scannées et non du texte sélectionnable :

```bash
# Installer OCRmyPDF
sudo apt install -y ocrmypdf

# Convertir avec OCR
ocrmypdf --force-ocr aide-tp.pdf aide-tp-ocr.pdf
ocrmypdf --force-ocr projet.pdf projet-ocr.pdf
ocrmypdf --force-ocr tutoriel-bdw-server.pdf tutoriel-bdw-server-ocr.pdf

# Puis convertir en markdown
pdftotext aide-tp-ocr.pdf - | pandoc -f plain -t markdown -o aide-tp.md
pdftotext projet-ocr.pdf - | pandoc -f plain -t markdown -o projet.md
pdftotext tutoriel-bdw-server-ocr.pdf - | pandoc -f plain -t markdown -o tutoriel-bdw-server.md
```

## Vérification des résultats

Après la conversion, vérifiez les fichiers créés :

```bash
ls -lh *.md
```

Pour voir un aperçu :
```bash
head -n 20 aide-tp.md
head -n 20 projet.md
head -n 20 tutoriel-bdw-server.md
```

## Outils alternatifs

Si les résultats ne sont pas satisfaisants, vous pouvez essayer :

### marker-pdf (outil moderne avec IA)
```bash
pip install marker-pdf
marker_single /home/fneuf/projects/docs/aide-tp.pdf /home/fneuf/projects/docs/ --output_format markdown
```

### pdf2md (outil Python)
```bash
pip install pdf2md
pdf2md aide-tp.pdf
```

## Dépannage

**Problème : "Command not found"**
- Solution : Installez les outils manquants avec `sudo apt install poppler-utils pandoc`

**Problème : Le fichier MD est vide ou mal formaté**
- Solution : Le PDF pourrait être une image scannée, utilisez la méthode 4 avec OCR

**Problème : Erreurs de formatage dans le markdown**
- Solution : Essayez marker-pdf qui gère mieux la mise en page complexe

---

## Exécution rapide (copier-coller)

Pour une conversion rapide, copiez et collez cette commande dans votre terminal WSL :

```bash
cd /home/fneuf/projects/docs && for pdf in aide-tp.pdf projet.pdf tutoriel-bdw-server.pdf; do pdftotext "$pdf" - | pandoc -f plain -t markdown -o "${pdf%.pdf}.md" && echo "✅ ${pdf%.pdf}.md créé"; done
```

