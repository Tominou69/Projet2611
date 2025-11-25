#!/usr/bin/env python3
"""
Script Python pur pour convertir les PDFs en Markdown
Utilise pypdf pour extraire le texte sans dépendances externes
"""
import os
import sys

# Installation des dépendances si nécessaire
try:
    from pypdf import PdfReader
except ImportError:
    print("📦 Installation de pypdf...")
    import subprocess
    subprocess.check_call([sys.executable, "-m", "pip", "install", "pypdf"])
    from pypdf import PdfReader

def extract_text_from_pdf(pdf_path):
    """Extrait le texte d'un PDF"""
    try:
        reader = PdfReader(pdf_path)
        text = ""
        total_pages = len(reader.pages)
        
        print(f"   📖 Extraction du texte ({total_pages} pages)...")
        
        for i, page in enumerate(reader.pages, 1):
            page_text = page.extract_text()
            if page_text:
                text += page_text + "\n\n"
            
            if i % 10 == 0:
                print(f"   Progression: {i}/{total_pages} pages")
        
        return text.strip()
    except Exception as e:
        print(f"   ❌ Erreur lors de l'extraction: {e}")
        return None

def format_as_markdown(text, title):
    """Formate le texte en Markdown"""
    # Nettoyer le texte
    lines = text.split('\n')
    cleaned_lines = []
    
    for line in lines:
        line = line.strip()
        if line:
            cleaned_lines.append(line)
    
    # Créer le contenu Markdown avec en-tête
    markdown_content = f"# {title}\n\n"
    markdown_content += "---\n\n"
    
    # Ajouter le contenu avec formatage basique
    current_paragraph = []
    
    for line in cleaned_lines:
        # Détecter les titres potentiels (lignes courtes en majuscules)
        if len(line) < 100 and line.isupper() and len(line.split()) <= 10:
            if current_paragraph:
                markdown_content += ' '.join(current_paragraph) + "\n\n"
                current_paragraph = []
            markdown_content += f"## {line.title()}\n\n"
        # Détecter les listes à puces
        elif line.startswith(('•', '-', '*', '○')):
            if current_paragraph:
                markdown_content += ' '.join(current_paragraph) + "\n\n"
                current_paragraph = []
            markdown_content += f"- {line.lstrip('•-*○ ')}\n"
        # Ligne normale
        else:
            current_paragraph.append(line)
            # Si la ligne se termine par un point, commencer un nouveau paragraphe
            if line.endswith(('.', '!', '?', ':', ';')):
                markdown_content += ' '.join(current_paragraph) + "\n\n"
                current_paragraph = []
    
    # Ajouter le dernier paragraphe
    if current_paragraph:
        markdown_content += ' '.join(current_paragraph) + "\n"
    
    return markdown_content

def convert_pdf_to_md(pdf_file):
    """Convertit un PDF en Markdown"""
    base_name = os.path.splitext(pdf_file)[0]
    md_file = f"{base_name}.md"
    
    print(f"\n📄 Traitement de {pdf_file}")
    
    # Vérifier que le fichier existe
    if not os.path.exists(pdf_file):
        print(f"   ❌ Fichier non trouvé: {pdf_file}")
        return False
    
    # Extraire le texte
    text = extract_text_from_pdf(pdf_file)
    
    if not text:
        print(f"   ❌ Impossible d'extraire le texte de {pdf_file}")
        return False
    
    print(f"   ✓ Texte extrait: {len(text)} caractères")
    
    # Formater en Markdown
    markdown_content = format_as_markdown(text, base_name)
    
    # Sauvegarder le fichier
    try:
        with open(md_file, 'w', encoding='utf-8') as f:
            f.write(markdown_content)
        
        file_size = os.path.getsize(md_file)
        print(f"   ✅ {md_file} créé avec succès! ({file_size} octets)")
        
        # Afficher un aperçu
        lines = markdown_content.split('\n')[:10]
        print(f"   📋 Aperçu:")
        for line in lines[:5]:
            if line.strip():
                preview = line[:70] + "..." if len(line) > 70 else line
                print(f"      {preview}")
        
        return True
    except Exception as e:
        print(f"   ❌ Erreur lors de l'écriture de {md_file}: {e}")
        return False

def main():
    print("=" * 60)
    print("🔄 Conversion des PDFs en Markdown")
    print("=" * 60)
    
    # Déterminer le répertoire de travail
    docs_dir = "/home/fneuf/projects/docs"
    
    # Si on est sur Windows, utiliser le chemin WSL
    if os.name == 'nt' or sys.platform == 'win32':
        # Essayer différents chemins
        possible_paths = [
            r"\\wsl.localhost\Ubuntu\home\fneuf\projects\docs",
            r"\\wsl$\Ubuntu\home\fneuf\projects\docs",
            "docs",
            "."
        ]
        
        for path in possible_paths:
            if os.path.exists(path):
                docs_dir = path
                break
    
    print(f"\n📂 Répertoire de travail: {docs_dir}")
    
    try:
        os.chdir(docs_dir)
        print(f"✓ Changement vers: {os.getcwd()}\n")
    except Exception as e:
        print(f"⚠️  Impossible de changer vers {docs_dir}, utilisation du répertoire courant")
        print(f"   Répertoire actuel: {os.getcwd()}\n")
    
    # Liste des PDFs à convertir
    pdf_files = ["aide-tp.pdf", "projet.pdf", "tutoriel-bdw-server.pdf"]
    
    # Trouver les PDFs existants
    existing_pdfs = []
    for pdf in pdf_files:
        if os.path.exists(pdf):
            existing_pdfs.append(pdf)
        else:
            print(f"⚠️  Fichier non trouvé: {pdf}")
    
    if not existing_pdfs:
        print("\n❌ Aucun fichier PDF trouvé!")
        print("\nFichiers disponibles dans le répertoire:")
        for file in os.listdir('.'):
            if file.endswith('.pdf'):
                print(f"   - {file}")
        sys.exit(1)
    
    print(f"📋 Fichiers à convertir: {len(existing_pdfs)}")
    for pdf in existing_pdfs:
        print(f"   • {pdf}")
    
    # Convertir chaque PDF
    success_count = 0
    failed = []
    
    for pdf in existing_pdfs:
        if convert_pdf_to_md(pdf):
            success_count += 1
        else:
            failed.append(pdf)
    
    # Résumé
    print("\n" + "=" * 60)
    print(f"✨ Conversion terminée!")
    print(f"   ✅ Réussis: {success_count}/{len(existing_pdfs)}")
    
    if failed:
        print(f"   ❌ Échoués: {', '.join(failed)}")
    
    # Lister les fichiers markdown créés
    md_files = [f for f in os.listdir('.') if f.endswith('.md') and 
                f.replace('.md', '.pdf') in existing_pdfs]
    
    if md_files:
        print(f"\n📝 Fichiers Markdown créés:")
        for md in sorted(md_files):
            size = os.path.getsize(md)
            print(f"   • {md} ({size:,} octets)")
    
    print("=" * 60)

if __name__ == "__main__":
    main()

