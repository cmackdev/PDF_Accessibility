# PDF Accessibility Tool - Known Limitations

This document provides detailed information about the limitations, constraints, and expected behaviors of the PDF Accessibility Remediation Tool. Understanding these limitations will help you make informed decisions about which PDFs to process and what results to expect.

## Table of Contents

- [File Size Impact](#file-size-impact)
- [Form Tag Behavior](#form-tag-behavior)
- [Accessibility Issues Requiring Manual Review](#accessibility-issues-requiring-manual-review)
- [Performance Considerations](#performance-considerations)
- [Processing Constraints](#processing-constraints)
- [Best Practices](#best-practices)

---

## File Size Impact

### Overview

The PDF Accessibility Tool adds structural tags, metadata, and accessibility features to PDFs, which can affect file size. The impact varies significantly based on the complexity and existing structure of your documents.

### Expected File Size Changes

#### Simple PDFs (Text and Images Only)

**Characteristics:**
- Primarily text content with basic images
- No interactive forms or complex structures
- Minimal existing accessibility tags

**Expected Impact:**
- **File size may increase up to 25%** due to merge pipeline overhead
- Compression applied during merge operations minimizes size impact
- Example: A 2MB simple document may result in a 2.0-2.5MB output
- Smaller PDFs experience proportionally larger overhead (metadata, structure)

**Why Size May Increase:**
- PDF merge pipeline adds metadata and cross-references
- Accessibility tags add structural information
- Overhead is proportionally larger for smaller files

**Why Size May Reduce (for larger documents):**
- PDF compression removes redundant data
- Object stream compression optimizes internal structure
- Duplicate resources are consolidated

#### Complex PDFs with Forms

**Characteristics:**
- Interactive form fields (text boxes, checkboxes, dropdowns)
- Multiple layers and annotations
- Existing partial accessibility tags
- Complex page structures

**Expected Impact:**
- **File size may increase by 20-50%** of original size
- Example: A 5MB complex form may result in a 6-7.5MB output
- In rare cases with highly complex documents, increases up to 150% may occur

**Why Size Increases:**
- Addition of comprehensive accessibility tags for all elements
- Form field accessibility metadata (tooltips, descriptions, alternative text)
- Structural tags for reading order and document hierarchy
- Enhanced metadata for assistive technology compatibility

### File Size Examples

| Document Type | Input Size | Output Size | Change | Notes |
|--------------|-----------|-------------|--------|-------|
| Simple text PDF (small) | 1.0 KB | 1.2 KB | +20% | Merge overhead for small files |
| Simple text PDF (large) | 2.0 MB | 1.9 MB | -5% | Compression benefits |
| PDF with images | 8.5 MB | 8.7 MB | +2% | Minimal tag overhead |
| Form with 20 fields | 3.2 MB | 4.0 MB | +25% | Form accessibility tags |
| Complex multi-page form | 6.8 MB | 9.5 MB | +40% | Extensive tagging |
| Scanned document (OCR) | 15.0 MB | 16.5 MB | +10% | OCR text layer added |

### Validated Size Bounds

The following size bounds have been validated through property-based testing (100+ iterations each):

| PDF Type | Maximum Size Increase | Validated By |
|----------|----------------------|--------------|
| Simple PDFs (no forms) | 125% of original | Property Test 3 |
| Complex PDFs with forms | 150% of original | Property Test 2 |
| Compression operation | Never increases size | Property Test 1 |

### Monitoring File Size

The tool automatically logs file size metrics during processing:

```
Input file size: 5.2 MB
Pre-compression size: 7.8 MB
Final compressed size: 6.5 MB
Compression ratio: 125% of original
```

**CloudWatch Logs Location:**
- Java Lambda merge function: `/aws/lambda/PDFMergerLambda`
- Look for log entries containing "Compression" or "file size"

### Mitigation Strategies

If file size is a critical concern:

1. **Pre-process large PDFs**: Split documents into smaller logical sections before processing
2. **Evaluate necessity**: Only process PDFs that genuinely need accessibility improvements
3. **Test first**: Process a sample document to evaluate size impact before batch processing
4. **Consider PDF-to-HTML**: For web display, the HTML solution may be more efficient

---

## Form Tag Behavior

### Overview

The tool handles PDF form fields with special care to preserve existing accessibility features while adding missing tags. Understanding this behavior is crucial for documents with interactive forms.

### Form Tag Preservation

#### What Gets Preserved

The tool automatically detects and preserves the following form field properties:

- **Field Name (`/T`)**: The unique identifier for the form field
- **Tooltip/User Description (`/TU`)**: Help text displayed when hovering over the field
- **Mapping Name (`/TM`)**: Export name used when submitting form data
- **Alternative Text (`/Alt`)**: Description for screen readers
- **Widget Annotations**: Visual properties and accessibility attributes

#### Processing Workflow

```
1. Extract Form Tags
   ↓
   - Scan PDF for interactive form fields
   - Preserve all accessibility properties
   - Log: "Extracted N form field tags"

2. Apply Autotag
   ↓
   - Adobe PDF Services API adds structural tags
   - Document structure and reading order improved
   - Form fields temporarily lose custom tags

3. Restore Form Tags
   ↓
   - Reapply preserved form field properties
   - Verify all tags successfully restored
   - Log: "Restored N form field tags"
```

### When to Skip Processing

#### PDFs with Fully-Tagged Forms

**Indicators:**
- All form fields have tooltips and alternative text
- Form passes accessibility checkers (e.g., Adobe Acrobat Pro)
- Document already meets WCAG 2.1 Level AA for forms

**Recommendation:**
- **Skip processing** - existing tags are already compliant
- Processing will preserve tags but adds unnecessary overhead
- File size may increase without meaningful accessibility gains

**How to Check:**
1. Open PDF in Adobe Acrobat Pro
2. Go to Tools → Accessibility → Accessibility Check
3. Review form field accessibility results
4. If all form checks pass, processing may not be needed

#### PDFs with Partially-Tagged Forms

**Indicators:**
- Some form fields have accessibility tags, others don't
- Mixed compliance across different form elements
- Document partially meets accessibility standards

**Recommendation:**
- **Process the document** - tool will preserve existing tags and add missing ones
- Existing compliant tags remain intact
- Missing tags are added automatically
- Best of both worlds: preservation + enhancement

#### PDFs with Untagged Forms

**Indicators:**
- No form field accessibility properties
- Form fields lack tooltips and descriptions
- Accessibility checkers report form field issues

**Recommendation:**
- **Process the document** - tool will add comprehensive form accessibility
- All form fields receive proper tagging
- Significant accessibility improvement expected

### Form Tag Verification

Form tag preservation has been validated through property-based testing:

| Property | Validation | Test Iterations |
|----------|-----------|-----------------|
| Extraction completeness | All form field properties captured | 100+ |
| Preservation through processing | All tags restored after autotag | 100+ |

After processing, verify form tags were preserved:

**CloudWatch Logs:**
```
Extracted 15 form field tags
Restored 15 form field tags
Form tag preservation: SUCCESS
```

**Manual Verification:**
1. Open output PDF in Adobe Acrobat Pro
2. Right-click on form field → Properties
3. Check "Tooltip" and "Name" fields are populated
4. Verify accessibility checker passes form field tests

### Known Form Limitations

- **Dynamic XFA Forms**: Not fully supported; may require manual review
- **JavaScript-dependent Forms**: Behavior may change; test thoroughly
- **Calculated Fields**: Formulas preserved but verify calculations work
- **Digital Signatures**: Signature fields preserved but may need re-signing

---

## Accessibility Issues Requiring Manual Review

### Overview

While the PDF Accessibility Tool significantly improves document accessibility, certain complex issues require human judgment and manual correction. This section identifies what the tool handles automatically and what needs manual attention.

### Automatically Handled by the Tool

✅ **Structural Tags**: Document hierarchy (headings, paragraphs, lists)  
✅ **Reading Order**: Logical flow for screen readers  
✅ **Image Alt Text**: AI-generated descriptions for images  
✅ **Form Field Tags**: Accessibility properties for interactive elements  
✅ **OCR Text Layer**: Searchable text for scanned documents  
✅ **Metadata**: Document title, language, and properties  
✅ **Basic Tables**: Simple table structure and headers  

### Requires Manual Review and Correction

#### 1. Complex Tables

**Issue:**
- Multi-level headers (row and column spanning)
- Nested tables or tables within tables
- Tables with irregular structures

**Why Manual Review Needed:**
- AI may misidentify table boundaries
- Header associations may be incorrect
- Complex relationships require human understanding

**How to Fix:**
1. Open PDF in Adobe Acrobat Pro
2. Use Tags panel to review table structure
3. Manually assign header cells and scope
4. Test with screen reader (NVDA, JAWS)

#### 2. Reading Order in Complex Layouts

**Issue:**
- Multi-column layouts with sidebars
- Text wrapping around images
- Magazine-style layouts with callout boxes

**Why Manual Review Needed:**
- Logical reading order may differ from visual layout
- Tool uses heuristics that may not match intended flow
- Context-dependent decisions required

**How to Fix:**
1. Use Adobe Acrobat Pro's Reading Order tool
2. Manually reorder content blocks
3. Test with screen reader to verify flow
4. Adjust as needed for logical comprehension

#### 3. Color Contrast Issues

**Issue:**
- Text with insufficient contrast against background
- Color-coded information without text alternatives
- Images with poor contrast

**Why Manual Review Needed:**
- Tool cannot modify image content or color schemes
- WCAG 2.1 requires 4.5:1 contrast ratio for normal text
- Automated detection may flag false positives

**How to Fix:**
1. Use color contrast analyzer tools
2. Modify source document colors if possible
3. Add text alternatives for color-coded information
4. Consider redesigning problematic sections

#### 4. Mathematical Equations and Formulas

**Issue:**
- Complex mathematical notation
- Chemical formulas and scientific symbols
- Equations rendered as images

**Why Manual Review Needed:**
- MathML or LaTeX markup may be needed
- Screen readers require proper mathematical structure
- Visual representation may not convey meaning

**How to Fix:**
1. Add alternative text describing the equation
2. Consider MathML tagging for complex formulas
3. Provide text explanation of mathematical concepts
4. Use accessible equation editors when possible

#### 5. Charts, Graphs, and Diagrams

**Issue:**
- Data visualizations with complex information
- Flowcharts and process diagrams
- Infographics with multiple data points

**Why Manual Review Needed:**
- AI-generated alt text may miss key insights
- Data tables may be needed as alternatives
- Context and interpretation require human judgment

**How to Fix:**
1. Review AI-generated alt text for accuracy
2. Add detailed descriptions of trends and patterns
3. Provide data tables as alternatives to charts
4. Include text summaries of key findings

#### 6. Decorative vs. Informative Images

**Issue:**
- Determining which images convey information
- Identifying purely decorative elements
- Context-dependent image significance

**Why Manual Review Needed:**
- AI cannot always determine image purpose
- Decorative images should be marked as artifacts
- Informative images need meaningful descriptions

**How to Fix:**
1. Review each image's purpose in context
2. Mark decorative images as artifacts (no alt text)
3. Ensure informative images have descriptive alt text
4. Remove redundant images when possible

#### 7. Document Language and Multilingual Content

**Issue:**
- Mixed-language documents
- Proper language tagging for each section
- Correct pronunciation for screen readers

**Why Manual Review Needed:**
- Tool sets primary document language
- Inline language changes need manual tagging
- Proper names and technical terms may need special handling

**How to Fix:**
1. Set primary document language in properties
2. Tag sections in different languages appropriately
3. Use language-specific tags for proper pronunciation
4. Test with screen readers in multiple languages

### Manual Review Checklist

After processing, review the following:

- [ ] Open document in Adobe Acrobat Pro
- [ ] Run full accessibility check (Tools → Accessibility)
- [ ] Review and fix any reported issues
- [ ] Test with screen reader (NVDA, JAWS, or VoiceOver)
- [ ] Verify reading order makes logical sense
- [ ] Check all images have appropriate alt text
- [ ] Verify form fields are properly labeled
- [ ] Test color contrast with analyzer tool
- [ ] Review complex tables for proper structure
- [ ] Validate document metadata is correct

### Recommended Tools for Manual Review

- **Adobe Acrobat Pro DC**: Comprehensive accessibility tools
- **PAC (PDF Accessibility Checker)**: Free validation tool
- **NVDA**: Free screen reader for Windows
- **JAWS**: Professional screen reader
- **Color Contrast Analyzer**: Free contrast checking tool
- **axe DevTools**: Browser extension for accessibility testing

---

## Performance Considerations

### Processing Time

#### Factors Affecting Processing Speed

**Document Complexity:**
- Simple PDFs: 30 seconds - 2 minutes
- Complex PDFs with forms: 2-5 minutes
- Large multi-page documents: 5-15 minutes
- Scanned documents requiring OCR: 10-30 minutes

**Document Size:**
- Small (<5 MB): Fast processing
- Medium (5-20 MB): Moderate processing time
- Large (20-100 MB): Slower processing, consider splitting
- Very Large (>100 MB): May timeout, splitting recommended

**Page Count:**
- 1-10 pages: Minimal impact
- 10-50 pages: Moderate processing time
- 50-200 pages: Longer processing, parallel chunks used
- 200+ pages: Significant time, batch processing recommended

### Concurrent Processing Limits

**PDF-to-PDF Solution:**
- **Maximum concurrent chunks**: 100 (Step Functions map state limit)
- **ECS task concurrency**: Limited by AWS account quotas
- **Lambda concurrency**: 1000 concurrent executions (default)

**Optimization:**
- Large PDFs automatically split into chunks for parallel processing
- Each chunk processed independently
- Results merged after all chunks complete

### Resource Consumption

#### AWS Lambda

**Java Merge Lambda:**
- Memory: 3008 MB allocated
- Timeout: 900 seconds (15 minutes)
- Typical execution: 30-120 seconds
- Cost: ~$0.05-0.20 per execution

**Python Autotag Lambda:**
- Memory: 2048 MB allocated
- Timeout: 900 seconds
- Typical execution: 60-300 seconds
- Cost: ~$0.10-0.40 per execution

#### ECS Fargate Tasks

**Autotag Container:**
- CPU: 2 vCPU
- Memory: 4 GB
- Typical runtime: 2-10 minutes per chunk
- Cost: ~$0.10-0.50 per task

**Alt Text Generation Container:**
- CPU: 2 vCPU
- Memory: 4 GB
- Typical runtime: 1-5 minutes per chunk
- Cost: ~$0.08-0.30 per task

### Cost Optimization Strategies

1. **Batch Processing**: Process multiple PDFs together to amortize overhead
2. **Off-Peak Processing**: Schedule large batches during low-cost periods
3. **Selective Processing**: Only process PDFs that need accessibility improvements
4. **Pre-filtering**: Skip PDFs that already meet accessibility standards
5. **Chunk Size Tuning**: Adjust split parameters for optimal parallelization

### Timeout Considerations

**When Timeouts May Occur:**
- Very large PDFs (>100 MB) with complex structures
- Documents with thousands of images requiring alt text
- Network issues with Adobe PDF Services API
- High concurrent load on AWS services

**Mitigation:**
- Split large documents before processing
- Increase Lambda timeout if needed (max 15 minutes)
- Implement retry logic for transient failures
- Monitor CloudWatch logs for timeout patterns

### Monitoring Performance

**CloudWatch Metrics to Track:**
- Lambda execution duration
- ECS task runtime
- Step Functions execution time
- S3 upload/download times
- API call latencies

**Performance Alerts:**
Set up CloudWatch alarms for:
- Lambda timeouts (>800 seconds)
- ECS task failures
- Step Functions execution failures
- Unusually long processing times

### Scaling Considerations

**Horizontal Scaling:**
- Step Functions automatically parallelizes chunk processing
- ECS tasks scale based on workload
- Lambda functions scale automatically

**Vertical Scaling:**
- Increase Lambda memory for faster processing
- Increase ECS task CPU/memory for complex documents
- Adjust chunk size for optimal parallelization

**Limits to Consider:**
- AWS account service quotas
- Elastic IP limits for ECS tasks
- S3 request rate limits
- Adobe API rate limits

---

## Processing Constraints

### Document Requirements

**Supported PDF Versions:**
- PDF 1.4 through 2.0
- Older versions may have limited support

**Unsupported Features:**
- Password-protected PDFs (must be unlocked first)
- Encrypted PDFs with restrictions
- Corrupted or malformed PDFs
- PDFs with digital rights management (DRM)

### Adobe PDF Services API Limitations

**API Constraints:**
- Maximum file size: 100 MB per API call
- Rate limits apply (varies by license tier)
- Network connectivity required
- API credentials must be valid and active

**Workarounds:**
- Split large files before processing
- Implement retry logic for rate limits
- Monitor API usage and quotas

### AWS Service Limits

**S3:**
- Maximum object size: 5 TB
- Multipart upload recommended for >100 MB files

**Lambda:**
- Maximum execution time: 15 minutes
- Maximum memory: 10 GB
- Deployment package size: 250 MB (unzipped)

**ECS Fargate:**
- Maximum task runtime: No hard limit, but monitor costs
- CPU/memory combinations: Specific valid pairs only

**Step Functions:**
- Maximum execution time: 1 year (effectively unlimited)
- Maximum concurrent executions: 1,000,000
- Map state concurrency: 100 (configurable)

---

## Best Practices

### Before Processing

1. **Evaluate Document Needs**
   - Run accessibility check on original PDF
   - Identify specific accessibility gaps
   - Determine if processing is necessary

2. **Test with Sample Documents**
   - Process one representative document first
   - Verify output quality and file size
   - Adjust expectations based on results

3. **Prepare Documents**
   - Unlock password-protected PDFs
   - Remove unnecessary pages or content
   - Consider splitting very large documents

### During Processing

1. **Monitor Progress**
   - Check CloudWatch logs for errors
   - Track Step Functions execution status
   - Watch for timeout warnings

2. **Manage Costs**
   - Process during off-peak hours if possible
   - Batch similar documents together
   - Avoid reprocessing already-compliant PDFs

### After Processing

1. **Validate Results**
   - Run accessibility checker on output
   - Compare file sizes with expectations
   - Test with screen readers

2. **Manual Review**
   - Check complex elements (tables, charts)
   - Verify reading order is logical
   - Test form functionality if applicable

3. **Document Findings**
   - Note any manual corrections needed
   - Track processing metrics for future reference
   - Share feedback to improve the tool

### Troubleshooting Tips

**If Processing Fails:**
1. Check CloudWatch logs for error messages
2. Verify input PDF is not corrupted
3. Ensure Adobe API credentials are valid
4. Check AWS service quotas and limits
5. Try processing a smaller test document

**If Output Quality is Poor:**
1. Review manual correction requirements
2. Consider alternative processing approaches
3. Evaluate if source document needs improvement
4. Test with different PDF versions or formats

**If File Size is Excessive:**
1. Verify compression is being applied
2. Check if document has unnecessary embedded content
3. Consider splitting into smaller logical sections
4. Evaluate if processing is truly necessary

---

## Additional Resources

- [README.md](../README.md) - Main documentation and deployment guide
- [BATCH_PROCESSING.md](BATCH_PROCESSING.md) - Guide for processing multiple PDFs
- [IAM_PERMISSIONS.md](IAM_PERMISSIONS.md) - Required AWS permissions
- [TROUBLESHOOTING_CDK_DEPLOY.md](TROUBLESHOOTING_CDK_DEPLOY.md) - Deployment troubleshooting

## Support

For questions or issues related to these limitations:

- **Email**: ai-cic@amazon.com
- **GitHub Issues**: [PDF_Accessibility Issues](https://github.com/ASUCICREPO/PDF_Accessibility/issues)

---

**Last Updated**: December 2024  
**Version**: 1.0
