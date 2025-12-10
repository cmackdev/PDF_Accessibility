# Release Notes

## Version Update: V4  
**Release Date:** December 2024  

### Bug Fixes and Improvements:

#### 1. File Size Optimization
- **Added PDF compression** to the Java Lambda merge function using PDFBox PDF 1.5 object streams
- **Compression logging** now tracks input size, pre-compression size, and final size with compression ratio
- **Fallback logic** ensures uncompressed merge is used if compression fails
- **Property-based testing** validates compression behavior across 100+ test iterations

#### 2. Form Tag Preservation
- **New form tag extraction** preserves field names, tooltips, mapping names, and alternative text before autotagging
- **Automatic restoration** of form field accessibility properties after Adobe PDF Services API processing
- **Verification logging** confirms all form tags are successfully preserved
- **Property-based testing** validates form tag preservation through the complete pipeline

#### 3. Enhanced Documentation
- **"When to Use This Tool"** section added to README with suitable/unsuitable PDF types
- **"Known Limitations"** section documents file size impacts and form tag behavior
- **LIMITATIONS.md** provides detailed guidance on expected file size changes and manual review requirements
- **BATCH_PROCESSING.md** guide for S3 sync workflows, monitoring, and CloudWatch queries

#### 4. File Size Expectations (Updated)
- **Simple PDFs**: May increase up to 25% due to merge pipeline overhead
- **Complex PDFs with forms**: May increase up to 50% (within 150% bound)
- **Note**: Smaller PDFs experience proportionally larger overhead; larger documents benefit more from compression

---

## Version Update: V3  
**Release Date:** TBD  

### Key Features:
- **Automated Deployment**: Streamlined deployment process with automated scripts
- **PDF2HTML Functionality**: New capability to convert PDFs to accessible HTML format

---

## Version Update: V2  
**Release Date:** 14 Feb 2025  

---

## Key Updates:

### 1. Model Upgrade  
- Transitioned from **Claude** to **Nova** models for better adaptability to current requirements.

### 2. Enhanced Spatial Context for Alt Text  
- Alt text for images now incorporates **spatial context** by analyzing surrounding content near the Image.  
- This improvement ensures more descriptive and contextually relevant alt text, leading to better accessibility.

### 3. Improved Mathematical Alt Text Descriptions  
- Updated prompting strategies to enhance alt text descriptions for **Math Equations**.

### 4. General Performance Improvements  
- Refactored our code for better readability in **AutoTag Docker**.  
- Removed unused dependencies.

---

For further details or inquiries, please refer to the documentation or contact our support team.


