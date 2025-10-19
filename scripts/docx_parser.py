"""
Advanced Word Document Parser for Department 56 Gallery
Intelligently extracts houses and accessories from Word documents

Author: GitHub Copilot
Date: October 18, 2025
"""

import os
import re
import json
from pathlib import Path
from typing import Dict, List, Optional, Tuple
from dataclasses import dataclass, asdict
from docx import Document
from docx.text.paragraph import Paragraph
from docx.shape import InlineShape
from PIL import Image
import io

@dataclass
class ExtractedItem:
    """Represents an extracted house or accessory"""
    name: str
    item_type: str  # 'house' or 'accessory'
    sku: Optional[str] = None
    description: Optional[str] = None
    notes: Optional[str] = None
    price: Optional[float] = None
    year: Optional[int] = None
    purchased_year: Optional[int] = None
    image_data: Optional[bytes] = None
    image_filename: Optional[str] = None
    linked_items: List[str] = None  # Names of linked items
    
    def __post_init__(self):
        if self.linked_items is None:
            self.linked_items = []


class SmartDocxParser:
    """
    Intelligent parser for Department 56 Word documents
    """
    
    # Patterns for extracting information
    SKU_PATTERNS = [
        r'(?:SKU|Item\s*#|Item\s*Number)[\s:]*([A-Z0-9.-]+)',
        r'\b(\d{2,3}\.\d{4,5})\b',  # Direct SKU format like 56.12345
    ]
    
    PRICE_PATTERNS = [
        r'\$\s*(\d+(?:\.\d{2})?)',
        r'(?:Price|Cost|MSRP)[\s:]*\$?\s*(\d+(?:\.\d{2})?)',
    ]
    
    YEAR_PATTERNS = [
        r'(?:Released?|Introduced?)[\s:]*(\d{4})',
        r'\b(19\d{2}|20\d{2})\b',  # 1900s or 2000s
    ]
    
    PURCHASED_YEAR_PATTERNS = [
        r'(?:Purchased?|Bought|Acquired)[\s:]*(\d{4})',
    ]
    
    LINK_PATTERNS = [
        r'(?:coordinates?\s+with|goes\s+with|pairs?\s+with|accessory\s+for|works?\s+with)[:\s]+([^.]+)',
        r'(?:house|building)[:\s]+([^.]+)',  # When in accessory section
    ]
    
    # Keywords that indicate sections or noise
    BOX_KEYWORDS = ['box', 'packaging', 'container', 'original box']
    IGNORE_LINES = ['imported from docx', 'page break', '']
    
    def __init__(self, output_dir: str = "parsed_output"):
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(exist_ok=True)
        self.image_dir = self.output_dir / "images"
        self.image_dir.mkdir(exist_ok=True)
    
    def parse_document(self, docx_path: str) -> Dict:
        """
        Parse a Word document and extract houses and accessories
        
        Returns:
            Dictionary with 'houses' and 'accessories' lists
        """
        print(f"\n{'='*60}")
        print(f"Parsing: {Path(docx_path).name}")
        print(f"{'='*60}\n")
        
        doc = Document(docx_path)
        
        # Extract all content
        pages = self._split_into_pages(doc)
        
        houses = []
        accessories = []
        
        # Process Page 1 (House)
        if len(pages) > 0:
            house = self._parse_page_1(pages[0], Path(docx_path).stem)
            if house:
                houses.append(house)
                print(f"✓ Extracted house: {house.name}")
        
        # Process remaining pages (Accessories)
        for i, page in enumerate(pages[1:], start=2):
            accessory = self._parse_accessory_page(page, i, Path(docx_path).stem)
            if accessory:
                accessories.append(accessory)
                print(f"✓ Extracted accessory: {accessory.name}")
        
        result = {
            'source_file': Path(docx_path).name,
            'houses': [asdict(h) for h in houses],
            'accessories': [asdict(a) for a in accessories],
        }
        
        # Print summary
        print(f"\n{'─'*60}")
        print(f"Summary:")
        print(f"  Houses: {len(houses)}")
        print(f"  Accessories: {len(accessories)}")
        print(f"{'─'*60}\n")
        
        return result
    
    def _split_into_pages(self, doc: Document) -> List[List]:
        """Split document into pages based on page breaks"""
        pages = [[]]
        
        for element in doc.element.body:
            # Check for page break
            if element.tag.endswith('p'):  # Paragraph
                para = Paragraph(element, doc)
                
                # Check if this paragraph contains a page break
                if self._has_page_break(para):
                    if pages[-1]:  # Only start new page if current page has content
                        pages.append([])
                else:
                    pages[-1].append(para)
            
            # Handle tables, images, etc.
            else:
                pages[-1].append(element)
        
        return [p for p in pages if p]  # Remove empty pages
    
    def _has_page_break(self, paragraph: Paragraph) -> bool:
        """Check if paragraph contains a page break"""
        for run in paragraph.runs:
            if 'w:br' in run._element.xml and 'w:type="page"' in run._element.xml:
                return True
        return False
    
    def _parse_page_1(self, page_content: List, doc_name: str) -> Optional[ExtractedItem]:
        """Parse first page to extract house information"""
        text_lines = []
        images = []
        
        # Extract text (skip images for now)
        for element in page_content:
            if isinstance(element, Paragraph):
                text = element.text.strip()
                if text and not self._should_ignore_line(text):
                    text_lines.append(text)
        
        if len(text_lines) < 2:
            print("  ⚠ Warning: Page 1 has insufficient text")
            return None
        
        # Line 1: House name
        house_name = text_lines[0]
        
        # Line 2: Accessory name (we'll use this for linking)
        accessory_name = text_lines[1] if len(text_lines) > 1 else None
        
        # Line 3: May be box info (ignore if so)
        start_idx = 2
        if len(text_lines) > 2 and self._is_box_line(text_lines[2]):
            start_idx = 3
        
        # Remaining lines: Extract details
        details_text = ' '.join(text_lines[start_idx:])
        
        house = ExtractedItem(
            name=house_name,
            item_type='house',
            sku=self._extract_sku(details_text),
            description=self._extract_description(details_text, house_name),
            notes=self._extract_notes(details_text),
            price=self._extract_price(details_text),
            year=self._extract_year(details_text),
            purchased_year=self._extract_purchased_year(details_text),
            linked_items=[accessory_name] if accessory_name else [],
        )
        
        # Save image if found
        if images:
            house.image_data = images[0]  # Use first image
            house.image_filename = self._generate_image_filename(house_name, 'house')
            self._save_image(house.image_data, house.image_filename)
        
        return house
    
    def _parse_accessory_page(self, page_content: List, page_num: int, doc_name: str) -> Optional[ExtractedItem]:
        """Parse accessory page"""
        text_lines = []
        images = []
        
        # Extract text (skip images for now)
        for element in page_content:
            if isinstance(element, Paragraph):
                text = element.text.strip()
                if text and not self._should_ignore_line(text):
                    text_lines.append(text)
        
        if not text_lines:
            print(f"  ⚠ Warning: Page {page_num} has no text")
            return None
        
        # Line 1: Accessory name
        accessory_name = text_lines[0]
        
        # Remaining lines: Extract details
        details_text = ' '.join(text_lines[1:])
        
        accessory = ExtractedItem(
            name=accessory_name,
            item_type='accessory',
            sku=self._extract_sku(details_text),
            description=self._extract_description(details_text, accessory_name),
            notes=self._extract_notes(details_text),
            price=self._extract_price(details_text),
            purchased_year=self._extract_purchased_year(details_text),
            linked_items=self._extract_links(details_text),
        )
        
        # Save image if found
        if images:
            accessory.image_data = images[0]
            accessory.image_filename = self._generate_image_filename(accessory_name, 'accessory')
            self._save_image(accessory.image_data, accessory.image_filename)
        
        return accessory
    
    def _extract_sku(self, text: str) -> Optional[str]:
        """Extract SKU/Item number from text"""
        for pattern in self.SKU_PATTERNS:
            match = re.search(pattern, text, re.IGNORECASE)
            if match:
                return match.group(1)
        return None
    
    def _extract_price(self, text: str) -> Optional[float]:
        """Extract price from text"""
        for pattern in self.PRICE_PATTERNS:
            match = re.search(pattern, text, re.IGNORECASE)
            if match:
                try:
                    return float(match.group(1))
                except ValueError:
                    continue
        return None
    
    def _extract_year(self, text: str) -> Optional[int]:
        """Extract release year from text"""
        for pattern in self.YEAR_PATTERNS:
            match = re.search(pattern, text, re.IGNORECASE)
            if match:
                try:
                    year = int(match.group(1))
                    if 1990 <= year <= 2030:  # Reasonable range
                        return year
                except ValueError:
                    continue
        return None
    
    def _extract_purchased_year(self, text: str) -> Optional[int]:
        """Extract purchased year from text"""
        for pattern in self.PURCHASED_YEAR_PATTERNS:
            match = re.search(pattern, text, re.IGNORECASE)
            if match:
                try:
                    year = int(match.group(1))
                    if 1990 <= year <= 2030:
                        return year
                except ValueError:
                    continue
        return None
    
    def _extract_description(self, text: str, item_name: str) -> Optional[str]:
        """Extract description from text"""
        # Remove the item name from text
        text = text.replace(item_name, '').strip()
        
        # Remove SKU, price, year mentions
        text = re.sub(r'(?:SKU|Item\s*#|Item\s*Number)[\s:]*[A-Z0-9.-]+', '', text, flags=re.IGNORECASE)
        text = re.sub(r'\$\s*\d+(?:\.\d{2})?', '', text)
        text = re.sub(r'(?:Released?|Introduced?|Purchased?)[\s:]*\d{4}', '', text, flags=re.IGNORECASE)
        
        # Extract first few sentences as description
        sentences = re.split(r'[.!?]', text)
        if sentences:
            desc = sentences[0].strip()
            if len(desc) > 20:  # Meaningful description
                return desc
        
        return None
    
    def _extract_notes(self, text: str) -> Optional[str]:
        """Extract additional notes from text"""
        # For now, return the full text as notes
        # You can refine this to extract specific sections
        notes = text.strip()
        return notes if notes else None
    
    def _extract_links(self, text: str) -> List[str]:
        """Extract linked item names from text"""
        links = []
        for pattern in self.LINK_PATTERNS:
            matches = re.findall(pattern, text, re.IGNORECASE)
            links.extend(matches)
        return [link.strip() for link in links]
    
    def _extract_image(self, inline_shape: InlineShape) -> Optional[bytes]:
        """Extract image data from inline shape"""
        try:
            # Get the image blob
            image = inline_shape._inline.graphic.graphicData.pic.blipFill.blip.embed
            # This is a relationship ID, not the actual image
            # You'll need to resolve it through the document's relationships
            # For simplicity, we'll skip this for now
            return None
        except Exception as e:
            print(f"    ⚠ Could not extract image: {e}")
            return None
    
    def _generate_image_filename(self, item_name: str, item_type: str) -> str:
        """Generate a filename for the image"""
        # Clean the name for use in filename
        clean_name = re.sub(r'[^a-zA-Z0-9\s-]', '', item_name)
        clean_name = re.sub(r'\s+', '_', clean_name)
        return f"{item_type}_{clean_name.lower()}.jpg"
    
    def _save_image(self, image_data: bytes, filename: str):
        """Save image to disk"""
        if not image_data:
            return
        
        try:
            img_path = self.image_dir / filename
            with open(img_path, 'wb') as f:
                f.write(image_data)
            print(f"    💾 Saved image: {filename}")
        except Exception as e:
            print(f"    ⚠ Could not save image: {e}")
    
    def _should_ignore_line(self, line: str) -> bool:
        """Check if line should be ignored"""
        line_lower = line.lower()
        return any(keyword in line_lower for keyword in self.IGNORE_LINES)
    
    def _is_box_line(self, line: str) -> bool:
        """Check if line is about box/packaging"""
        line_lower = line.lower()
        return any(keyword in line_lower for keyword in self.BOX_KEYWORDS)
    
    def save_results(self, results: Dict, output_filename: str):
        """Save parsing results to JSON"""
        output_path = self.output_dir / output_filename
        with open(output_path, 'w', encoding='utf-8') as f:
            json.dump(results, f, indent=2, ensure_ascii=False)
        print(f"\n✅ Results saved to: {output_path}")


def main():
    """Main function to test the parser"""
    import sys
    
    if len(sys.argv) < 2:
        print("Usage: python docx_parser.py <path_to_docx_file>")
        print("\nExample:")
        print('  python docx_parser.py "\\\\DilgerNAS\\Public\\Media\\Day NP Files\\A Stitch in Yule Time 2019 She\'ll Be Belle of the Ball.docx"')
        sys.exit(1)
    
    docx_path = sys.argv[1]
    
    if not os.path.exists(docx_path):
        print(f"❌ Error: File not found: {docx_path}")
        sys.exit(1)
    
    parser = SmartDocxParser()
    results = parser.parse_document(docx_path)
    
    # Display detailed results in terminal
    print("\n" + "="*70)
    print("EXTRACTED DATA REVIEW")
    print("="*70)
    
    # Display houses
    for house in results['houses']:
        print("\n🏠 HOUSE")
        print("─"*70)
        print(f"  Name:           {house['name']}")
        print(f"  SKU:            {house['sku'] or '(not found)'}")
        print(f"  Description:    {house['description'] or '(not found)'}")
        print(f"  Price:          ${house['price']:.2f}" if house['price'] else "  Price:          (not found)")
        print(f"  Released Year:  {house['year'] or '(not found)'}")
        print(f"  Purchased Year: {house['purchased_year'] or '(not found)'}")
        print(f"  Linked Items:   {', '.join(house['linked_items']) if house['linked_items'] else '(none)'}")
        if house['notes']:
            print(f"  Notes Preview:  {house['notes'][:100]}...")
    
    # Display accessories
    for accessory in results['accessories']:
        print("\n🎨 ACCESSORY")
        print("─"*70)
        print(f"  Name:           {accessory['name']}")
        print(f"  SKU:            {accessory['sku'] or '(not found)'}")
        print(f"  Description:    {accessory['description'] or '(not found)'}")
        print(f"  Price:          ${accessory['price']:.2f}" if accessory['price'] else "  Price:          (not found)")
        print(f"  Purchased Year: {accessory['purchased_year'] or '(not found)'}")
        print(f"  Linked Items:   {', '.join(accessory['linked_items']) if accessory['linked_items'] else '(none)'}")
        if accessory['notes']:
            print(f"  Notes Preview:  {accessory['notes'][:100]}...")
    
    # Save results
    output_filename = f"parsed_{Path(docx_path).stem}.json"
    parser.save_results(results, output_filename)
    
    print("\n" + "="*70)
    print("PARSING COMPLETE")
    print("="*70)
    print(f"\n📄 Full details saved to: {parser.output_dir / output_filename}")
    print(f"\nReview the extracted data above and let me know if the parser")
    print(f"is correctly identifying all fields!")
    print()


if __name__ == "__main__":
    main()
