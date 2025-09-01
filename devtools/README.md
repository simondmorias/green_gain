# Entity Artifact Generation Tool

This tool generates entity artifacts from Databricks for the Live Intent Highlighting feature in the Gain platform.

## Setup

1. **Install dependencies:**
   ```bash
   pip install -r requirements.txt
   ```

2. **Configure environment variables:**
   ```bash
   cp .env.example .env
   # Edit .env with your Databricks credentials
   ```

3. **Databricks credentials:**
   - `DATABRICKS_HOST`: Your Databricks workspace URL
   - `DATABRICKS_HTTP_PATH`: SQL warehouse HTTP path
   - `DATABRICKS_TOKEN`: Personal access token

## Usage

### Basic usage (generate artifacts):
```bash
python generate_entity_artifacts.py
```

### Dry run (test without writing files):
```bash
python generate_entity_artifacts.py --dry-run
```

### Push to Redis cache:
```bash
python generate_entity_artifacts.py --push-redis
```

### Verbose logging:
```bash
python generate_entity_artifacts.py --verbose
```

### Combine options:
```bash
python generate_entity_artifacts.py --push-redis --verbose
```

## Output

The script generates two artifact files:

1. **gazetteer.json** - Entity lists organized by type
   - Location: `/gain/apps/api/app/data/artifacts/gazetteer.json`
   - Structure:
     ```json
     {
       "entities": {
         "manufacturers": ["Cadbury", "Thorntons", ...],
         "brands": ["Dairy Milk", "Galaxy", ...],
         "categories": ["Chocolate Bars", ...],
         "products": ["Milk Chocolate", ...]
       },
       "metrics": ["revenue", "market share", ...],
       "timewords": ["Q1", "Q2", "YTD", ...],
       "special_tokens": ["vs", "compare", ...]
     }
     ```

2. **aliases.jsonl** - Entity name variations (one JSON object per line)
   - Location: `/gain/apps/api/app/data/artifacts/aliases.jsonl`
   - Structure:
     ```json
     {"type": "manufacturer", "name": "Cadbury", "alias": "cadburys", "id": "MFR_001", "confidence": 0.9}
     {"type": "manufacturer", "name": "Cadbury", "alias": "cadbury's", "id": "MFR_001", "confidence": 0.9}
     ```

## Data Source

The script connects to the Databricks table:
- Catalog: `rgm_poc`
- Schema: `chocolate`
- Table: `master_product_hierarchy`

It extracts:
- **Manufacturers**: Brand entities at level 0
- **Brands**: Brand entities at level 1
- **Categories**: Category entities at level 0
- **Products**: Category entities at levels 1-3 (needstates, segments, subsegments)

## Performance

Target metrics:
- Completion time: < 2 minutes
- Total artifact size: < 10MB
- Entity coverage: 100% of active entities in master table

## Redis Caching (Optional)

When using `--push-redis`, artifacts are cached with:
- Keys: `entity:gazetteer` and `entity:aliases`
- TTL: 24 hours
- Format: JSON strings

## Troubleshooting

### Connection errors:
- Verify Databricks credentials in `.env`
- Check network connectivity to Databricks workspace
- Ensure SQL warehouse is running

### Large artifact size:
- Review entity filtering criteria
- Consider excluding inactive entities
- Optimize alias generation rules

### Slow performance:
- Check Databricks warehouse size
- Optimize SQL query
- Consider caching intermediate results

## Scheduling

For production use, schedule daily runs:

```cron
# Run daily at 2 AM UTC
0 2 * * * cd /path/to/gain/devtools && python generate_entity_artifacts.py --push-redis
```

## Development

To extend the script:

1. **Add new entity types**: Modify `extract_entities()` method
2. **Customize aliases**: Update `_create_variations()` method
3. **Add metrics**: Extend the metrics list in `build_gazetteer()`
4. **Change output format**: Modify `save_artifacts()` method

## Testing

Run in dry-run mode to test without side effects:
```bash
python generate_entity_artifacts.py --dry-run --verbose
```

This will:
- Use sample data instead of real Databricks connection
- Skip file writes
- Skip Redis pushes
- Show verbose logging