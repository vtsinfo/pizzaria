import re
from datetime import datetime
from io import BytesIO
import pypdf

def extract_invoice_data(file_stream):
    """
    Extracts data from a PDF file stream.
    Returns a dict with:
    - cnpj_fornecedor
    - numero_nota
    - data_emissao
    - itens: list of {codigo, descricao, quantidade, valor_unitario, valor_total}
    """
    try:
        reader = pypdf.PdfReader(file_stream)
        text = ""
        for page in reader.pages:
            text += page.extract_text() + "\n"
        
        # Basic Cleanup
        lines = [line.strip() for line in text.split('\n') if line.strip()]
        full_text = " ".join(lines)

        data = {
            "cnpj_fornecedor": None,
            "numero_nota": None,
            "data_emissao": None,
            "itens": []
        }

        # 1. Extract CNPJ (Pattern: XX.XXX.XXX/YYYY-ZZ)
        cnpj_match = re.search(r'\d{2}\.\d{3}\.\d{3}/\d{4}-\d{2}', full_text)
        if cnpj_match:
            data["cnpj_fornecedor"] = cnpj_match.group(0)

        # 2. Extract Invoice Number (Patterns like "Nota Nº 123" or just "Nº 123")
        # Trying a few common patterns
        nf_pattern = re.search(r'(?:Nota|N[º°o])\s*[:.]?\s*(\d{3,9})', full_text, re.IGNORECASE)
        if nf_pattern:
            data["numero_nota"] = nf_pattern.group(1)

        # 3. Extract Date (Pattern: DD/MM/YYYY)
        date_match = re.search(r'(\d{2}/\d{2}/\d{4})', full_text)
        if date_match:
            try:
                # Validate date format
                datetime.strptime(date_match.group(1), '%d/%m/%Y')
                data["data_emissao"] = date_match.group(1) # Send as string YYYY-MM-DD ideally, but leaving formatted for frontend to parse or standardizing here
                
                # Convert to YYYY-MM-DD for HTML input
                dt = datetime.strptime(date_match.group(1), '%d/%m/%Y')
                data["data_emissao"] = dt.strftime('%Y-%m-%d')
            except:
                pass

        # 4. Attempt to find items
        # This is the hardest part without spatial analysis. 
        # Strategy: Look for lines that end with a number (total) and have a quantity and unit price before it.
        # Example Line: "Refrigerante Coca Cola 2L  UN  10,00  8,50  85,00"
        
        for line in lines:
            # Simple heuristic: Ends with a monetary value? (X,XX or X.XX)
            # Regex for money like 10,00 or 1.000,00: (\d{1,3}(?:\.\d{3})*,\d{2})
            
            # Let's try to find a pattern: Desc... Qty... Unit... Total
            # We assume Qty is a number, Unit Price is money, Total is money.
            
            # Weak regex for item line: 
            # (Description) (Qty as int/float) (Unit Price) (Total)
            # This is very specific to layout, usually fails generically.
            # We'll try a generous match: Look for lines with at least 3 numbers at the end.
            
            # Pattern: Any text followed by Number Number Number (Qty, Unit, Total)
            # Handling pt-BR number format (comma decimal)
            
            parts = line.split()
            if len(parts) < 4:
                continue
                
            # Try to parse the last 3 tokens as numbers
            try:
                # Helper to convert "1.000,00" to float 1000.00
                def parse_br_float(s):
                    return float(s.replace('.', '').replace(',', '.'))

                val_total = parse_br_float(parts[-1])
                val_unit = parse_br_float(parts[-2])
                
                # Qty might be index -3 or -4 if there is a Unit string like 'UN' or 'KG'
                # Let's try to detect if parts[-3] is a unit string
                
                potential_qty = parts[-3]
                desc_end_index = -3
                
                # Check if potential_qty is a number. If not, maybe it's "UN", "KG", then qty is before.
                if not re.match(r'^\d+([.,]\d+)?$', potential_qty): 
                    # potential_qty is likely a unit (UN, KG, L)
                    potential_qty = parts[-4]
                    desc_end_index = -4
                
                qty = parse_br_float(potential_qty)
                
                # Check math: Qty * Unit ~= Total (allow small rounding error)
                if abs((qty * val_unit) - val_total) < 0.2:
                    # Found a match!
                    description = " ".join(parts[:desc_end_index])
                    
                    data["itens"].append({
                        "descricao": description,
                        "quantidade": qty,
                        "preco_unitario": val_unit,
                        "subtotal": val_total
                    })
                    
            except:
                continue

        return data

    except Exception as e:
        print(f"Error parsing PDF: {e}")
        return None
