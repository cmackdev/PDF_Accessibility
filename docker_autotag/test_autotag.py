"""
Property-based tests for form tag preservation in autotag.py

These tests validate that form field accessibility properties are correctly
extracted and restored during the PDF autotagging process.
"""

import os
import tempfile
from typing import Dict, Any
from pypdf import PdfReader, PdfWriter
from pypdf.generic import DictionaryObject, ArrayObject, IndirectObject, NameObject, TextStringObject
from hypothesis import given, strategies as st, settings, assume
import pytest

from autotag import extract_form_tags, restore_form_tags


# Strategy for generating form field names
field_names = st.text(min_size=1, max_size=50, alphabet=st.characters(
    whitelist_categories=('Lu', 'Ll', 'Nd'),
    whitelist_characters='_-'
))

# Strategy for generating optional text properties
optional_text = st.one_of(
    st.none(),
    st.text(min_size=0, max_size=200)
)


def create_pdf_with_form_fields(field_data: Dict[str, Dict[str, Any]]) -> str:
    """
    Create a temporary PDF with form fields containing specified properties.
    
    Args:
        field_data: Dictionary mapping field names to their properties
        
    Returns:
        Path to the created temporary PDF file
    """
    # Create a simple PDF with one page
    writer = PdfWriter()
    writer.add_blank_page(width=612, height=792)  # Letter size
    
    # Create AcroForm dictionary
    acro_form = DictionaryObject()
    fields_array = ArrayObject()
    
    for field_name, properties in field_data.items():
        # Create field dictionary
        field = DictionaryObject()
        field.update({
            NameObject("/T"): TextStringObject(field_name),
            NameObject("/FT"): NameObject("/Tx"),  # Text field type
        })
        
        # Add optional properties
        if properties.get("tooltip"):
            field[NameObject("/TU")] = TextStringObject(properties["tooltip"])
        
        if properties.get("mapping_name"):
            field[NameObject("/TM")] = TextStringObject(properties["mapping_name"])
        
        if properties.get("alt_text"):
            field[NameObject("/Alt")] = TextStringObject(properties["alt_text"])
        
        fields_array.append(field)
    
    acro_form[NameObject("/Fields")] = fields_array
    writer._root_object[NameObject("/AcroForm")] = acro_form
    
    # Write to temporary file
    temp_fd, temp_path = tempfile.mkstemp(suffix=".pdf")
    os.close(temp_fd)
    
    with open(temp_path, "wb") as f:
        writer.write(f)
    
    return temp_path


@given(
    field_name=field_names,
    tooltip=optional_text,
    mapping_name=optional_text,
    alt_text=optional_text
)
@settings(max_examples=100, deadline=None)
def test_form_tag_extraction_completeness(field_name, tooltip, mapping_name, alt_text):
    """
    **Feature: pdf-accessibility-bug-fixes, Property 4: Form tag extraction is complete**
    **Validates: Requirements 2.1, 2.2**
    
    For any PDF with form fields, the extraction function should capture all form field
    accessibility properties (field name, tooltip, mapping name, alt text).
    """
    # Skip if field name is empty after stripping
    assume(field_name.strip() != "")
    
    # Create test data
    field_data = {
        field_name: {
            "tooltip": tooltip,
            "mapping_name": mapping_name,
            "alt_text": alt_text
        }
    }
    
    # Create PDF with form field
    pdf_path = create_pdf_with_form_fields(field_data)
    
    try:
        # Extract form tags
        extracted_tags = extract_form_tags(pdf_path)
        
        # Verify the field was extracted
        assert field_name in extracted_tags, f"Field {field_name} was not extracted"
        
        extracted_field = extracted_tags[field_name]
        
        # Verify all properties were captured
        assert "field_name" in extracted_field, "field_name property missing"
        assert extracted_field["field_name"] == field_name, "field_name mismatch"
        
        # Verify tooltip
        if tooltip:
            assert "tooltip" in extracted_field, "tooltip property missing"
            assert extracted_field["tooltip"] == tooltip, "tooltip mismatch"
        
        # Verify mapping_name
        if mapping_name:
            assert "mapping_name" in extracted_field, "mapping_name property missing"
            assert extracted_field["mapping_name"] == mapping_name, "mapping_name mismatch"
        
        # Verify alt_text
        if alt_text:
            assert "alt_text" in extracted_field, "alt_text property missing"
            assert extracted_field["alt_text"] == alt_text, "alt_text mismatch"
        
    finally:
        # Clean up
        if os.path.exists(pdf_path):
            os.unlink(pdf_path)


@given(
    field_name=field_names,
    tooltip=optional_text,
    mapping_name=optional_text,
    alt_text=optional_text
)
@settings(max_examples=100, deadline=None)
def test_form_tags_preserved_through_processing(field_name, tooltip, mapping_name, alt_text):
    """
    **Feature: pdf-accessibility-bug-fixes, Property 5: Form tags are preserved through processing**
    **Validates: Requirements 2.3, 2.4, 2.5**
    
    For any PDF with form fields, after extraction, autotagging, and restoration, all original
    form field accessibility properties should be present in the output PDF.
    """
    # Skip if field name is empty after stripping
    assume(field_name.strip() != "")
    
    # Create test data
    field_data = {
        field_name: {
            "tooltip": tooltip,
            "mapping_name": mapping_name,
            "alt_text": alt_text
        }
    }
    
    # Create PDF with form field
    pdf_path = create_pdf_with_form_fields(field_data)
    
    try:
        # Step 1: Extract form tags
        extracted_tags = extract_form_tags(pdf_path)
        
        # Verify extraction worked
        assert field_name in extracted_tags, f"Field {field_name} was not extracted"
        
        # Step 2: Simulate processing by modifying the PDF
        # (In real scenario, this would be the autotag API call)
        # We'll just rewrite the PDF to simulate processing
        reader = PdfReader(pdf_path)
        writer = PdfWriter()
        for page in reader.pages:
            writer.add_page(page)
        
        # Copy the AcroForm
        if "/AcroForm" in reader.trailer["/Root"]:
            writer._root_object[NameObject("/AcroForm")] = reader.trailer["/Root"]["/AcroForm"]
        
        with open(pdf_path, "wb") as f:
            writer.write(f)
        
        # Step 3: Restore form tags
        restore_form_tags(pdf_path, extracted_tags)
        
        # Step 4: Verify all properties are present in the output
        final_reader = PdfReader(pdf_path)
        
        # Check if AcroForm exists
        assert "/AcroForm" in final_reader.trailer["/Root"], "AcroForm missing after restoration"
        
        acro_form = final_reader.trailer["/Root"]["/AcroForm"]
        assert "/Fields" in acro_form, "Fields missing in AcroForm"
        
        fields = acro_form["/Fields"]
        
        # Find our field
        field_found = False
        for field_ref in fields:
            field = field_ref.get_object()
            if str(field.get("/T", "")) == field_name:
                field_found = True
                
                # Verify tooltip was preserved
                if tooltip:
                    assert "/TU" in field, f"Tooltip missing for field {field_name}"
                    assert str(field["/TU"]) == tooltip, f"Tooltip mismatch for field {field_name}"
                
                # Verify mapping_name was preserved
                if mapping_name:
                    assert "/TM" in field, f"Mapping name missing for field {field_name}"
                    assert str(field["/TM"]) == mapping_name, f"Mapping name mismatch for field {field_name}"
                
                # Verify alt_text was preserved
                if alt_text:
                    assert "/Alt" in field, f"Alt text missing for field {field_name}"
                    assert str(field["/Alt"]) == alt_text, f"Alt text mismatch for field {field_name}"
                
                break
        
        assert field_found, f"Field {field_name} not found in restored PDF"
        
    finally:
        # Clean up
        if os.path.exists(pdf_path):
            os.unlink(pdf_path)


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
