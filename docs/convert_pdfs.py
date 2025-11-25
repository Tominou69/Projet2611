#!/usr/bin/env python3
"""
Script Python pour convertir les PDFs en Markdown
"""
import subprocess
import os
import sys

def run_command(cmd):
    """Exécute une commande et retourne le résultat"""
    try:
        result = subprocess.run(
            cmd,
            shell=True,
            check=True,
            capture_output=True,
            text=True
        )
        return True, result.stdout
    except subprocess.CalledProcessError as e:
        return False, e.stderr

def check_and_install_tools():
    """Vérifie et installe les outils nécessaires"""
    print("🔍 Vérification des outils nécessaires...")
    
    # Vérifier pdftotext
    success, _ = run_command("which pdftotext")
    if not success:
        print("📦 Installation de poppler-utils...")
        run_command("sudo apt update && sudo apt install -y poppler-utils")
    
    # Vérifier pandoc
    success, _ = run_command("which pandoc")
    if not success:
        print("📦 Installation de pandoc...")
        run_command("sudo apt update && sudo apt install -y pandoc")
    
    print("✅ Outils prêts!\n")

def convert_pdf_to_md(pdf_file):
    """Convertit un PDF en Markdown"""
    base_name = pdf_file.replace('.pdf', '')
    md_file = f"{base_name}.md"
    
    print(f"📄 Conversion de {pdf_file}...")
    
    # Convertir PDF en texte puis en markdown
    cmd = f"pdftotext '{pdf_file}' - | pandoc -f plain -t markdown -o '{md_file}'"
    success, output = run_command(cmd)
    
    if success:
        # Ajouter un en-tête au fichier
        try:
            with open(md_file, 'r', encoding='utf-8') as f:
                content = f.read()
            
            with open(md_file, 'w', encoding='utf-8') as f:
                f.write(f"# {base_name}\n\n---\n\n{content}")
            
            print(f"✅ {md_file} créé avec succès!")
            
            # Afficher un aperçu
            with open(md_file, 'r', encoding='utf-8') as f:
                lines = f.readlines()[:5]
                print("   Aperçu:")
                for line in lines:
                    print(f"   {line.rstrip()}")
            print()
            return True
        except Exception as e:
            print(f"❌ Erreur lors du traitement de {md_file}: {e}")
            return False
    else:
        print(f"❌ Erreur lors de la conversion de {pdf_file}")
        print(f"   {output}")
        return False

def main():
    # Changer vers le répertoire docs
    docs_dir = "/home/fneuf/projects/docs"
    
    try:
        os.chdir(docs_dir)
        print(f"📂 Répertoire de travail: {os.getcwd()}\n")
    except Exception as e:
        print(f"❌ Impossible de changer vers {docs_dir}: {e}")
        sys.exit(1)
    
    # Vérifier/installer les outils
    check_and_install_tools()
    
    # Liste des PDFs à convertir
    pdf_files = ["aide-tp.pdf", "projet.pdf", "tutoriel-bdw-server.pdf"]
    
    # Vérifier que les fichiers existent
    existing_pdfs = [f for f in pdf_files if os.path.exists(f)]
    
    if not existing_pdfs:
        print("❌ Aucun fichier PDF trouvé!")
        sys.exit(1)
    
    print(f"📋 Fichiers à convertir: {', '.join(existing_pdfs)}\n")
    
    # Convertir chaque PDF
    success_count = 0
    for pdf in existing_pdfs:
        if convert_pdf_to_md(pdf):
            success_count += 1
    
    print(f"\n✨ Conversion terminée! {success_count}/{len(existing_pdfs)} fichiers convertis.")
    
    # Lister les fichiers créés
    md_files = [f for f in os.listdir('.') if f.endswith('.md')]
    if md_files:
        print(f"\n📝 Fichiers markdown créés:")
        for md in md_files:
            size = os.path.getsize(md)
            print(f"   - {md} ({size} octets)")

if __name__ == "__main__":
    main()

