#!/bin/bash
# Script bash pour convertir les PDFs en Markdown
# Assurez-vous d'avoir installé poppler-utils et pandoc

echo "Conversion des PDFs en Markdown..."
echo "=================================="

# Vérifier si les outils nécessaires sont installés
if ! command -v pdftotext &> /dev/null; then
    echo "❌ pdftotext n'est pas installé"
    echo "Installation de poppler-utils..."
    sudo apt update && sudo apt install -y poppler-utils
fi

if ! command -v pandoc &> /dev/null; then
    echo "❌ pandoc n'est pas installé"
    echo "Installation de pandoc..."
    sudo apt update && sudo apt install -y pandoc
fi

# Changer vers le répertoire docs
cd /home/fneuf/projects/docs

# Liste des fichiers PDF
pdf_files=("aide-tp.pdf" "projet.pdf" "tutoriel-bdw-server.pdf")

# Convertir chaque PDF
for pdf in "${pdf_files[@]}"; do
    if [ -f "$pdf" ]; then
        base_name="${pdf%.pdf}"
        md_file="${base_name}.md"
        
        echo ""
        echo "📄 Traitement de $pdf..."
        
        # Méthode 1 : Conversion via pdftotext + pandoc
        pdftotext "$pdf" - | pandoc -f plain -t markdown -o "$md_file"
        
        if [ $? -eq 0 ]; then
            echo "✅ $md_file créé avec succès"
            
            # Ajouter un en-tête au fichier markdown
            temp_file=$(mktemp)
            echo "# ${base_name}" > "$temp_file"
            echo "" >> "$temp_file"
            echo "---" >> "$temp_file"
            echo "" >> "$temp_file"
            cat "$md_file" >> "$temp_file"
            mv "$temp_file" "$md_file"
            
            # Afficher les premières lignes
            echo "Aperçu des premières lignes:"
            head -n 5 "$md_file"
        else
            echo "❌ Erreur lors de la conversion de $pdf"
        fi
    else
        echo "⚠️  Fichier $pdf non trouvé"
    fi
done

echo ""
echo "✨ Conversion terminée !"
echo "Les fichiers markdown ont été créés dans: $(pwd)"

