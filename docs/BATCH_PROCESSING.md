# PDF Accessibility Tool - Batch Processing Guide

This guide provides comprehensive instructions for processing multiple PDF documents efficiently using the PDF Accessibility Remediation Tool. Whether you need to process dozens or thousands of PDFs, this guide will help you set up, monitor, and optimize your batch processing workflow.

## Table of Contents

- [Overview](#overview)
- [S3 Sync Workflow for Bulk Processing](#s3-sync-workflow-for-bulk-processing)
- [Monitoring Multiple Files](#monitoring-multiple-files)
- [Best Practices for Large Batches](#best-practices-for-large-batches)
- [Example Commands](#example-commands)
- [CloudWatch Queries](#cloudwatch-queries)
- [Troubleshooting Batch Processing](#troubleshooting-batch-processing)
- [Cost Optimization](#cost-optimization)

---

## Overview

### What is Batch Processing?

Batch processing allows you to upload and process multiple PDF documents simultaneously, leveraging the parallel processing capabilities of AWS Step Functions and ECS Fargate. The PDF Accessibility Tool automatically handles:

- **Parallel processing** of up to 100 PDF chunks concurrently
- **Automatic triggering** when files are uploaded to S3
- **Independent processing** of each document (failures don't affect others)
- **Organized output** with clear naming conventions

### When to Use Batch Processing

**Ideal Scenarios:**
- Processing document archives (10-1000+ PDFs)
- Migrating legacy document repositories to accessible formats
- Regular scheduled accessibility updates
- Department-wide document remediation projects

**Considerations:**
- Each PDF processes independently
- Processing time scales with document complexity, not quantity
- AWS service quotas may limit extreme concurrency
- Costs scale linearly with number of documents

---

## S3 Sync Workflow for Bulk Processing

### Step 1: Prepare Your Local Documents

Organize your PDF files in a local directory structure:

```bash
# Create a local directory for your PDFs
mkdir -p ~/pdf-batch-processing
cd ~/pdf-batch-processing

# Organize files (optional but recommended)
mkdir -p simple-pdfs
mkdir -p complex-pdfs
mkdir -p forms

# Move or copy your PDFs into appropriate folders
cp /path/to/your/pdfs/*.pdf simple-pdfs/
```

### Step 2: Identify Your S3 Bucket

Find your PDF Accessibility bucket name:

```bash
# List buckets with 'pdfaccessibility' in the name
aws s3 ls | grep pdfaccessibility

# Example output:
# 2024-12-09 10:30:45 pdfaccessibility-bucket-abc123def456
```

Set your bucket name as an environment variable for convenience:

```bash
export PDF_BUCKET="pdfaccessibility-bucket-abc123def456"
```

### Step 3: Upload Files Using AWS S3 Sync

#### Basic Sync Command

Upload all PDFs from your local directory:

```bash
# Sync entire directory to S3 pdf/ folder
aws s3 sync ~/pdf-batch-processing/ s3://${PDF_BUCKET}/pdf/ \
  --exclude "*" \
  --include "*.pdf" \
  --include "*.PDF"
```

#### Sync with Progress Monitoring

For large batches, add progress indicators:

```bash
# Sync with progress output
aws s3 sync ~/pdf-batch-processing/ s3://${PDF_BUCKET}/pdf/ \
  --exclude "*" \
  --include "*.pdf" \
  --include "*.PDF" \
  --no-progress false
```

#### Sync Specific Subdirectories

Upload only specific document types:

```bash
# Upload only simple PDFs
aws s3 sync ~/pdf-batch-processing/simple-pdfs/ s3://${PDF_BUCKET}/pdf/simple/ \
  --include "*.pdf"

# Upload only forms
aws s3 sync ~/pdf-batch-processing/forms/ s3://${PDF_BUCKET}/pdf/forms/ \
  --include "*.pdf"
```

#### Dry Run (Test Before Upload)

Preview what will be uploaded without actually uploading:

```bash
# Dry run to see what would be uploaded
aws s3 sync ~/pdf-batch-processing/ s3://${PDF_BUCKET}/pdf/ \
  --exclude "*" \
  --include "*.pdf" \
  --dryrun
```

### Step 4: Verify Upload

Confirm files were uploaded successfully:

```bash
# List all PDFs in the bucket
aws s3 ls s3://${PDF_BUCKET}/pdf/ --recursive | grep ".pdf"

# Count total PDFs uploaded
aws s3 ls s3://${PDF_BUCKET}/pdf/ --recursive | grep ".pdf" | wc -l
```

### Step 5: Monitor Processing

Processing begins automatically when files are uploaded. See [Monitoring Multiple Files](#monitoring-multiple-files) section for detailed monitoring instructions.

### Step 6: Download Processed Results

After processing completes, download the remediated PDFs:

```bash
# Create local directory for results
mkdir -p ~/pdf-batch-results

# Download all processed PDFs
aws s3 sync s3://${PDF_BUCKET}/result/ ~/pdf-batch-results/ \
  --exclude "*" \
  --include "*.pdf"

# Verify download
ls -lh ~/pdf-batch-results/
```

---

## Monitoring Multiple Files

### Real-Time Monitoring with AWS Console

#### Step Functions Console

1. **Navigate to Step Functions**
   - Open AWS Console → Step Functions
   - Find your state machine (typically named `PDFAccessibilityStateMachine`)

2. **View Executions**
   - Click on the state machine name
   - View "Executions" tab
   - Each PDF has its own execution
   - Status indicators: Running (blue), Succeeded (green), Failed (red)

3. **Monitor Progress**
   - Click individual executions to see detailed progress
   - View which step is currently executing
   - Check execution time and resource usage

#### CloudWatch Dashboard

1. **Access Dashboard**
   - Open AWS Console → CloudWatch
   - Navigate to Dashboards
   - Select the PDF Accessibility dashboard (created during deployment)

2. **Key Metrics to Monitor**
   - Lambda invocation counts
   - ECS task execution counts
   - Step Functions execution status
   - Error rates and failures

### Command-Line Monitoring

#### Check Step Functions Executions

List recent executions:

```bash
# Get your state machine ARN
STATE_MACHINE_ARN=$(aws stepfunctions list-state-machines \
  --query "stateMachines[?contains(name, 'PDFAccessibility')].stateMachineArn" \
  --output text)

# List recent executions
aws stepfunctions list-executions \
  --state-machine-arn ${STATE_MACHINE_ARN} \
  --max-results 50 \
  --output table
```

Count executions by status:

```bash
# Count running executions
aws stepfunctions list-executions \
  --state-machine-arn ${STATE_MACHINE_ARN} \
  --status-filter RUNNING \
  --query 'length(executions)'

# Count succeeded executions
aws stepfunctions list-executions \
  --state-machine-arn ${STATE_MACHINE_ARN} \
  --status-filter SUCCEEDED \
  --query 'length(executions)'

# Count failed executions
aws stepfunctions list-executions \
  --state-machine-arn ${STATE_MACHINE_ARN} \
  --status-filter FAILED \
  --query 'length(executions)'
```

#### Monitor S3 Processing Status

Check how many files are in each stage:

```bash
# Count input PDFs
echo "Input PDFs:"
aws s3 ls s3://${PDF_BUCKET}/pdf/ --recursive | grep ".pdf" | wc -l

# Count temporary processing files
echo "Processing (temp):"
aws s3 ls s3://${PDF_BUCKET}/temp/ --recursive | grep ".pdf" | wc -l

# Count completed results
echo "Completed (result):"
aws s3 ls s3://${PDF_BUCKET}/result/ --recursive | grep ".pdf" | wc -l
```

#### Monitor Processing Script

Create a monitoring script for continuous updates:

```bash
#!/bin/bash
# Save as monitor_processing.sh

PDF_BUCKET="your-bucket-name-here"
STATE_MACHINE_ARN="your-state-machine-arn-here"

while true; do
  clear
  echo "=== PDF Accessibility Batch Processing Monitor ==="
  echo "Time: $(date)"
  echo ""
  
  echo "S3 File Counts:"
  echo "  Input PDFs:    $(aws s3 ls s3://${PDF_BUCKET}/pdf/ --recursive | grep ".pdf" | wc -l)"
  echo "  Processing:    $(aws s3 ls s3://${PDF_BUCKET}/temp/ --recursive | grep ".pdf" | wc -l)"
  echo "  Completed:     $(aws s3 ls s3://${PDF_BUCKET}/result/ --recursive | grep ".pdf" | wc -l)"
  echo ""
  
  echo "Step Functions Executions:"
  echo "  Running:       $(aws stepfunctions list-executions --state-machine-arn ${STATE_MACHINE_ARN} --status-filter RUNNING --query 'length(executions)')"
  echo "  Succeeded:     $(aws stepfunctions list-executions --state-machine-arn ${STATE_MACHINE_ARN} --status-filter SUCCEEDED --query 'length(executions)')"
  echo "  Failed:        $(aws stepfunctions list-executions --state-machine-arn ${STATE_MACHINE_ARN} --status-filter FAILED --query 'length(executions)')"
  echo ""
  echo "Press Ctrl+C to stop monitoring"
  
  sleep 30
done
```

Make it executable and run:

```bash
chmod +x monitor_processing.sh
./monitor_processing.sh
```

---

## Best Practices for Large Batches

### Pre-Processing Preparation

#### 1. Categorize Documents

Group PDFs by complexity for better resource planning:

```bash
# Organize by size
mkdir -p small-pdfs medium-pdfs large-pdfs

# Move files based on size
find . -name "*.pdf" -size -5M -exec mv {} small-pdfs/ \;
find . -name "*.pdf" -size +5M -size -20M -exec mv {} medium-pdfs/ \;
find . -name "*.pdf" -size +20M -exec mv {} large-pdfs/ \;
```

#### 2. Validate PDFs Before Upload

Check for corrupted or problematic PDFs:

```bash
# Install pdfinfo (part of poppler-utils)
# Ubuntu/Debian: sudo apt-get install poppler-utils
# macOS: brew install poppler

# Check all PDFs in directory
for pdf in *.pdf; do
  if ! pdfinfo "$pdf" > /dev/null 2>&1; then
    echo "Corrupted or invalid: $pdf"
  fi
done
```

#### 3. Remove Password Protection

The tool cannot process password-protected PDFs:

```bash
# Use qpdf to remove passwords (if you have the password)
qpdf --password=yourpassword --decrypt input.pdf output.pdf
```

### Processing Strategy

#### Staged Upload Approach

For very large batches (1000+ PDFs), upload in stages:

```bash
# Stage 1: Upload first 100 PDFs
aws s3 sync ~/pdf-batch-processing/ s3://${PDF_BUCKET}/pdf/batch1/ \
  --exclude "*" \
  --include "*.pdf" \
  --max-items 100

# Wait for processing to complete, then upload next batch
# Stage 2: Upload next 100 PDFs
aws s3 sync ~/pdf-batch-processing/ s3://${PDF_BUCKET}/pdf/batch2/ \
  --exclude "*" \
  --include "*.pdf" \
  --max-items 100
```

#### Time-Based Upload

Schedule uploads during off-peak hours:

```bash
# Create a cron job for overnight processing
# Edit crontab: crontab -e
# Add line (runs at 2 AM daily):
0 2 * * * /usr/local/bin/aws s3 sync ~/pdf-batch-processing/ s3://your-bucket/pdf/ --include "*.pdf"
```

#### Parallel Upload for Speed

Use parallel uploads for faster transfer:

```bash
# Install GNU parallel
# Ubuntu/Debian: sudo apt-get install parallel
# macOS: brew install parallel

# Upload files in parallel (8 concurrent uploads)
find ~/pdf-batch-processing -name "*.pdf" | \
  parallel -j 8 aws s3 cp {} s3://${PDF_BUCKET}/pdf/
```

### Resource Management

#### Monitor AWS Service Quotas

Check your account limits before large batches:

```bash
# Check Lambda concurrent executions quota
aws service-quotas get-service-quota \
  --service-code lambda \
  --quota-code L-B99A9384

# Check ECS tasks per service quota
aws service-quotas get-service-quota \
  --service-code ecs \
  --quota-code L-9EF96962
```

#### Request Quota Increases

For very large batches, request increases:

1. Navigate to AWS Service Quotas console
2. Search for relevant service (Lambda, ECS, Step Functions)
3. Request quota increase
4. Typical approval time: 24-48 hours

### Error Handling

#### Identify Failed Documents

List failed Step Functions executions:

```bash
# Get failed execution details
aws stepfunctions list-executions \
  --state-machine-arn ${STATE_MACHINE_ARN} \
  --status-filter FAILED \
  --max-results 50 \
  --output json > failed_executions.json

# Extract failed file names from execution input
cat failed_executions.json | jq -r '.executions[].name'
```

#### Retry Failed Documents

Re-upload only failed PDFs:

```bash
# Create a list of failed files
cat failed_executions.json | jq -r '.executions[].name' > failed_files.txt

# Re-upload failed files
while read filename; do
  aws s3 cp ~/pdf-batch-processing/${filename} s3://${PDF_BUCKET}/pdf/retry/
done < failed_files.txt
```

### Post-Processing Validation

#### Verify All Files Processed

Compare input and output counts:

```bash
# Count input files
INPUT_COUNT=$(aws s3 ls s3://${PDF_BUCKET}/pdf/ --recursive | grep ".pdf" | wc -l)

# Count output files
OUTPUT_COUNT=$(aws s3 ls s3://${PDF_BUCKET}/result/ --recursive | grep ".pdf" | wc -l)

echo "Input files: ${INPUT_COUNT}"
echo "Output files: ${OUTPUT_COUNT}"

if [ ${INPUT_COUNT} -eq ${OUTPUT_COUNT} ]; then
  echo "✓ All files processed successfully"
else
  echo "⚠ Missing $(( INPUT_COUNT - OUTPUT_COUNT )) files"
fi
```

#### Generate Processing Report

Create a summary of batch processing:

```bash
#!/bin/bash
# Save as generate_report.sh

echo "PDF Accessibility Batch Processing Report"
echo "Generated: $(date)"
echo "=========================================="
echo ""

echo "File Counts:"
echo "  Input PDFs:     $(aws s3 ls s3://${PDF_BUCKET}/pdf/ --recursive | grep ".pdf" | wc -l)"
echo "  Output PDFs:    $(aws s3 ls s3://${PDF_BUCKET}/result/ --recursive | grep ".pdf" | wc -l)"
echo ""

echo "Step Functions Executions:"
echo "  Total:          $(aws stepfunctions list-executions --state-machine-arn ${STATE_MACHINE_ARN} --query 'length(executions)')"
echo "  Succeeded:      $(aws stepfunctions list-executions --state-machine-arn ${STATE_MACHINE_ARN} --status-filter SUCCEEDED --query 'length(executions)')"
echo "  Failed:         $(aws stepfunctions list-executions --state-machine-arn ${STATE_MACHINE_ARN} --status-filter FAILED --query 'length(executions)')"
echo "  Running:        $(aws stepfunctions list-executions --state-machine-arn ${STATE_MACHINE_ARN} --status-filter RUNNING --query 'length(executions)')"
echo ""

echo "File Size Analysis:"
INPUT_SIZE=$(aws s3 ls s3://${PDF_BUCKET}/pdf/ --recursive --summarize | grep "Total Size" | awk '{print $3}')
OUTPUT_SIZE=$(aws s3 ls s3://${PDF_BUCKET}/result/ --recursive --summarize | grep "Total Size" | awk '{print $3}')
echo "  Input total:    $(numfmt --to=iec-i --suffix=B ${INPUT_SIZE})"
echo "  Output total:   $(numfmt --to=iec-i --suffix=B ${OUTPUT_SIZE})"
```

---

## Example Commands

### Complete Batch Processing Workflow

Here's a complete example workflow for processing 100 PDFs:

```bash
# 1. Set up environment variables
export PDF_BUCKET="pdfaccessibility-bucket-abc123def456"
export STATE_MACHINE_ARN="arn:aws:states:us-east-1:123456789012:stateMachine:PDFAccessibility"
export LOCAL_PDF_DIR="~/documents/accessibility-batch"
export RESULTS_DIR="~/documents/accessibility-results"

# 2. Validate PDFs locally
echo "Validating PDFs..."
for pdf in ${LOCAL_PDF_DIR}/*.pdf; do
  if ! pdfinfo "$pdf" > /dev/null 2>&1; then
    echo "Invalid PDF: $pdf"
  fi
done

# 3. Upload to S3
echo "Uploading PDFs to S3..."
aws s3 sync ${LOCAL_PDF_DIR}/ s3://${PDF_BUCKET}/pdf/ \
  --exclude "*" \
  --include "*.pdf" \
  --no-progress false

# 4. Monitor processing
echo "Monitoring processing (Ctrl+C to stop)..."
while true; do
  RUNNING=$(aws stepfunctions list-executions \
    --state-machine-arn ${STATE_MACHINE_ARN} \
    --status-filter RUNNING \
    --query 'length(executions)')
  
  SUCCEEDED=$(aws stepfunctions list-executions \
    --state-machine-arn ${STATE_MACHINE_ARN} \
    --status-filter SUCCEEDED \
    --query 'length(executions)')
  
  echo "$(date): Running: ${RUNNING}, Completed: ${SUCCEEDED}"
  
  if [ ${RUNNING} -eq 0 ]; then
    echo "All processing complete!"
    break
  fi
  
  sleep 60
done

# 5. Download results
echo "Downloading results..."
mkdir -p ${RESULTS_DIR}
aws s3 sync s3://${PDF_BUCKET}/result/ ${RESULTS_DIR}/ \
  --exclude "*" \
  --include "*.pdf"

# 6. Generate report
echo "Processing complete!"
echo "Input files: $(ls ${LOCAL_PDF_DIR}/*.pdf | wc -l)"
echo "Output files: $(ls ${RESULTS_DIR}/*.pdf | wc -l)"
```

### Selective Processing Examples

#### Process Only Large Files

```bash
# Upload only PDFs larger than 10MB
find ~/pdf-batch-processing -name "*.pdf" -size +10M -exec \
  aws s3 cp {} s3://${PDF_BUCKET}/pdf/large/ \;
```

#### Process Files Modified Recently

```bash
# Upload PDFs modified in last 7 days
find ~/pdf-batch-processing -name "*.pdf" -mtime -7 -exec \
  aws s3 cp {} s3://${PDF_BUCKET}/pdf/recent/ \;
```

#### Process Specific File Patterns

```bash
# Upload only files matching pattern (e.g., reports)
aws s3 sync ~/pdf-batch-processing/ s3://${PDF_BUCKET}/pdf/reports/ \
  --exclude "*" \
  --include "*report*.pdf" \
  --include "*Report*.pdf"
```

---

## CloudWatch Queries

### CloudWatch Logs Insights Queries

Access CloudWatch Logs Insights in AWS Console → CloudWatch → Logs → Insights

#### Query 1: Processing Time by Document

```
fields @timestamp, @message
| filter @message like /Processing complete/
| parse @message "File: * | Duration: * seconds" as filename, duration
| stats avg(duration) as avg_duration, max(duration) as max_duration, min(duration) as min_duration by filename
| sort avg_duration desc
```

#### Query 2: File Size Impact Analysis

```
fields @timestamp, @message
| filter @message like /Compression ratio/
| parse @message "Filename: * | Input: * MB | Output: * MB | Ratio: *%" as filename, input_size, output_size, ratio
| stats avg(ratio) as avg_ratio, max(ratio) as max_ratio, min(ratio) as min_ratio
| display avg_ratio, max_ratio, min_ratio
```

#### Query 3: Error Analysis

```
fields @timestamp, @message, @logStream
| filter @message like /ERROR/ or @message like /Exception/ or @message like /Failed/
| stats count() by @logStream
| sort count desc
```

#### Query 4: Form Tag Preservation

```
fields @timestamp, @message
| filter @message like /form field tags/
| parse @message "Extracted * form field tags" as extracted_count
| parse @message "Restored * form field tags" as restored_count
| stats sum(extracted_count) as total_extracted, sum(restored_count) as total_restored
```

#### Query 5: Processing Throughput

```
fields @timestamp
| filter @message like /Processing complete/
| stats count() as completed_documents by bin(5m)
| sort @timestamp desc
```

### CloudWatch Metrics Queries

#### Lambda Invocation Metrics

```bash
# Get Lambda invocation count for last hour
aws cloudwatch get-metric-statistics \
  --namespace AWS/Lambda \
  --metric-name Invocations \
  --dimensions Name=FunctionName,Value=PDFMergerLambda \
  --start-time $(date -u -d '1 hour ago' +%Y-%m-%dT%H:%M:%S) \
  --end-time $(date -u +%Y-%m-%dT%H:%M:%S) \
  --period 300 \
  --statistics Sum
```

#### Step Functions Execution Metrics

```bash
# Get Step Functions execution success rate
aws cloudwatch get-metric-statistics \
  --namespace AWS/States \
  --metric-name ExecutionsFailed \
  --dimensions Name=StateMachineArn,Value=${STATE_MACHINE_ARN} \
  --start-time $(date -u -d '24 hours ago' +%Y-%m-%dT%H:%M:%S) \
  --end-time $(date -u +%Y-%m-%dT%H:%M:%S) \
  --period 3600 \
  --statistics Sum
```

#### ECS Task Metrics

```bash
# Get ECS task count
aws cloudwatch get-metric-statistics \
  --namespace AWS/ECS \
  --metric-name CPUUtilization \
  --dimensions Name=ServiceName,Value=PDFAccessibilityService \
  --start-time $(date -u -d '1 hour ago' +%Y-%m-%dT%H:%M:%S) \
  --end-time $(date -u +%Y-%m-%dT%H:%M:%S) \
  --period 300 \
  --statistics Average
```

### Custom CloudWatch Dashboard

Create a custom dashboard for batch monitoring:

```json
{
  "widgets": [
    {
      "type": "metric",
      "properties": {
        "metrics": [
          [ "AWS/States", "ExecutionsStarted", { "stat": "Sum" } ],
          [ ".", "ExecutionsSucceeded", { "stat": "Sum" } ],
          [ ".", "ExecutionsFailed", { "stat": "Sum" } ]
        ],
        "period": 300,
        "stat": "Sum",
        "region": "us-east-1",
        "title": "Step Functions Executions"
      }
    },
    {
      "type": "metric",
      "properties": {
        "metrics": [
          [ "AWS/Lambda", "Invocations", { "stat": "Sum" } ],
          [ ".", "Errors", { "stat": "Sum" } ],
          [ ".", "Duration", { "stat": "Average" } ]
        ],
        "period": 300,
        "stat": "Sum",
        "region": "us-east-1",
        "title": "Lambda Performance"
      }
    }
  ]
}
```

Save this JSON and import via CloudWatch Console → Dashboards → Create dashboard → Actions → View/edit source.

---

## Troubleshooting Batch Processing

### Common Issues and Solutions

#### Issue 1: Some Files Not Processing

**Symptoms:**
- Input count doesn't match output count
- Some Step Functions executions stuck in "Running"

**Diagnosis:**
```bash
# Check for stuck executions
aws stepfunctions list-executions \
  --state-machine-arn ${STATE_MACHINE_ARN} \
  --status-filter RUNNING \
  --max-results 50
```

**Solutions:**
1. Check if files are corrupted or password-protected
2. Verify Lambda timeout settings (should be 900 seconds)
3. Check ECS task logs for errors
4. Manually stop stuck executions and retry

#### Issue 2: High Failure Rate

**Symptoms:**
- Many Step Functions executions showing "Failed" status
- Error messages in CloudWatch logs

**Diagnosis:**
```bash
# Get error details from failed executions
aws stepfunctions describe-execution \
  --execution-arn <failed-execution-arn> \
  --query 'cause'
```

**Solutions:**
1. Check Adobe API credentials are valid
2. Verify AWS service quotas not exceeded
3. Review CloudWatch logs for specific error messages
4. Ensure input PDFs meet requirements (not encrypted, valid format)

#### Issue 3: Slow Processing

**Symptoms:**
- Processing takes much longer than expected
- Low throughput (few documents per hour)

**Diagnosis:**
```bash
# Check concurrent execution limits
aws stepfunctions describe-state-machine \
  --state-machine-arn ${STATE_MACHINE_ARN} \
  --query 'definition' | jq '.States.ProcessChunks.MaxConcurrency'
```

**Solutions:**
1. Increase Step Functions map state concurrency (default: 100)
2. Check ECS task capacity and scale if needed
3. Verify network connectivity to Adobe API
4. Consider splitting very large PDFs before processing

#### Issue 4: Out of Memory Errors

**Symptoms:**
- Lambda functions timing out
- ECS tasks failing with OOM errors

**Diagnosis:**
```bash
# Check Lambda memory usage
aws logs filter-log-events \
  --log-group-name /aws/lambda/PDFMergerLambda \
  --filter-pattern "Memory Size"
```

**Solutions:**
1. Increase Lambda memory allocation (currently 3008 MB)
2. Increase ECS task memory (currently 4 GB)
3. Split large PDFs into smaller chunks
4. Process large files separately from batch

#### Issue 5: Cost Overruns

**Symptoms:**
- Unexpected AWS charges
- High resource utilization

**Diagnosis:**
```bash
# Check current month costs
aws ce get-cost-and-usage \
  --time-period Start=$(date -d "$(date +%Y-%m-01)" +%Y-%m-%d),End=$(date +%Y-%m-%d) \
  --granularity MONTHLY \
  --metrics BlendedCost \
  --group-by Type=SERVICE
```

**Solutions:**
1. Process during off-peak hours for lower costs
2. Reduce concurrent execution limits
3. Pre-filter documents that don't need processing
4. Use staged upload approach for large batches

### Getting Additional Help

If issues persist:

1. **Check CloudWatch Logs**
   - Lambda logs: `/aws/lambda/PDFMergerLambda`
   - ECS logs: `/ecs/PDFAccessibility`
   - Step Functions execution history

2. **Review Documentation**
   - [LIMITATIONS.md](LIMITATIONS.md) - Known limitations
   - [TROUBLESHOOTING_CDK_DEPLOY.md](TROUBLESHOOTING_CDK_DEPLOY.md) - Deployment issues
   - [README.md](../README.md) - General documentation

3. **Contact Support**
   - Email: ai-cic@amazon.com
   - GitHub Issues: [PDF_Accessibility Issues](https://github.com/ASUCICREPO/PDF_Accessibility/issues)

---

## Cost Optimization

### Understanding Batch Processing Costs

**Cost Components:**
- **Lambda**: Charged per invocation and execution time
- **ECS Fargate**: Charged per vCPU-hour and GB-hour
- **Step Functions**: Charged per state transition
- **S3**: Storage and data transfer costs
- **Adobe API**: Based on your license tier

### Cost Estimation

**Per-Document Cost Estimate:**
- Simple PDF: $0.05 - $0.15
- Complex PDF with forms: $0.15 - $0.40
- Large PDF (>50 pages): $0.40 - $1.00

**Batch Processing Example:**
- 100 simple PDFs: ~$10
- 100 complex PDFs: ~$25
- 1000 simple PDFs: ~$100

### Cost Reduction Strategies

#### 1. Pre-Filter Documents

Only process PDFs that need accessibility improvements:

```bash
# Check if PDF already has accessibility tags
pdfinfo document.pdf | grep "Tagged"

# Only upload untagged PDFs
for pdf in *.pdf; do
  if ! pdfinfo "$pdf" | grep -q "Tagged: yes"; then
    aws s3 cp "$pdf" s3://${PDF_BUCKET}/pdf/
  fi
done
```

#### 2. Schedule Off-Peak Processing

Process during low-cost periods:

```bash
# Schedule for overnight processing (2 AM - 6 AM)
# Add to crontab: crontab -e
0 2 * * * /path/to/batch_upload_script.sh
```

#### 3. Optimize Chunk Size

Adjust PDF splitting parameters for efficiency:
- Larger chunks = fewer Lambda invocations = lower cost
- Smaller chunks = more parallelism = faster processing
- Balance based on your priorities

#### 4. Use Reserved Capacity

For regular batch processing, consider:
- AWS Savings Plans for Lambda and Fargate
- Reserved capacity for predictable workloads
- Potential savings: 20-40%

#### 5. Monitor and Alert

Set up cost alerts to avoid surprises:

```bash
# Create billing alarm (requires SNS topic)
aws cloudwatch put-metric-alarm \
  --alarm-name pdf-processing-cost-alert \
  --alarm-description "Alert when PDF processing costs exceed $100" \
  --metric-name EstimatedCharges \
  --namespace AWS/Billing \
  --statistic Maximum \
  --period 86400 \
  --evaluation-periods 1 \
  --threshold 100 \
  --comparison-operator GreaterThanThreshold
```

---

## Additional Resources

- [README.md](../README.md) - Main documentation and deployment guide
- [LIMITATIONS.md](LIMITATIONS.md) - Known limitations and constraints
- [IAM_PERMISSIONS.md](IAM_PERMISSIONS.md) - Required AWS permissions
- [TROUBLESHOOTING_CDK_DEPLOY.md](TROUBLESHOOTING_CDK_DEPLOY.md) - Deployment troubleshooting

## Support

For questions or issues related to batch processing:

- **Email**: ai-cic@amazon.com
- **GitHub Issues**: [PDF_Accessibility Issues](https://github.com/ASUCICREPO/PDF_Accessibility/issues)

---

**Last Updated**: December 2024  
**Version**: 1.0
