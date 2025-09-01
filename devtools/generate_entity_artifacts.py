#!/usr/bin/env python3
"""
Entity Artifact Generation Script for Live Intent Highlighting

This script connects to Databricks, extracts entity data from the master product
hierarchy table, and generates JSON artifacts for entity recognition.

Usage:
    python generate_entity_artifacts.py [--dry-run] [--push-redis] [--verbose]
"""

import json
import os
import sys
import time
import argparse
import logging
from pathlib import Path
from typing import Dict, List, Set
from collections import defaultdict
from datetime import timedelta

try:
    from databricks import sql
except ImportError:
    print("Databricks SDK not installed. Please run: "
          "pip install databricks-sdk databricks-sql-connector")
    sys.exit(1)

try:
    import redis
except ImportError:
    redis = None
    print("Redis support not available. Install redis-py for caching features.")

from dotenv import load_dotenv

load_dotenv()

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


class EntityArtifactGenerator:
    """Generates entity artifacts from Databricks warehouse data."""

    def __init__(self, dry_run: bool = False, verbose: bool = False):
        self.dry_run = dry_run
        self.verbose = verbose
        if verbose:
            logger.setLevel(logging.DEBUG)

        self.catalog = "rgm_poc"
        self.schema = "chocolate"
        self.table = "master_product_hierarchy"

        self.output_dir = (Path(__file__).parent.parent / "apps" / "api" /
                          "app" / "data" / "artifacts")
        self.gazetteer_path = self.output_dir / "gazetteer.json"
        self.aliases_path = self.output_dir / "aliases.jsonl"

        self.entities = defaultdict(list)
        self.aliases = []

        self._setup_databricks_connection()

    def _setup_databricks_connection(self):
        """Initialize Databricks connection using SDK."""
        if self.dry_run:
            logger.info("Dry run mode - skipping Databricks connection setup")
            return

        try:
            self.workspace_host = os.getenv("DATABRICKS_HOST", "").rstrip("/")
            self.http_path = os.getenv("DATABRICKS_HTTP_PATH", "")
            self.token = os.getenv("DATABRICKS_TOKEN", "")

            if not all([self.workspace_host, self.http_path, self.token]):
                raise ValueError(
                    "Missing Databricks credentials. Please set DATABRICKS_HOST, "
                    "DATABRICKS_HTTP_PATH, and DATABRICKS_TOKEN environment variables."
                )

            logger.info(f"Connecting to Databricks at {self.workspace_host}")

        except Exception as e:
            logger.error(f"Failed to setup Databricks connection: {e}")
            raise

    def connect_to_databricks(self):
        """Create a connection to Databricks SQL warehouse."""
        return sql.connect(
            server_hostname=self.workspace_host.replace("https://", ""),
            http_path=self.http_path,
            access_token=self.token
        )

    def extract_entities(self) -> Dict[str, List[Dict]]:
        """Extract entities from master_product_hierarchy table."""
        if self.dry_run:
            logger.info("Dry run mode - using sample data")
            return self._get_sample_entities()

        logger.info(f"Extracting entities from {self.catalog}.{self.schema}.{self.table}")

        query = f"""
        SELECT
            product_hierarchy_key as id,
            level,
            description as name,
            hierarchy_name as type,
            parent_key as parent_id,
            CONCAT(hierarchy_name, '/', description) as hierarchy_path
        FROM {self.catalog}.{self.schema}.{self.table}
        WHERE description IS NOT NULL
        ORDER BY hierarchy_name, level
        """

        entities_by_type = {
            "manufacturers": [],
            "brands": [],
            "categories": [],
            "products": []
        }

        try:
            with self.connect_to_databricks() as conn:
                with conn.cursor() as cursor:
                    cursor.execute(query)
                    rows = cursor.fetchall()

                    logger.info(f"Retrieved {len(rows)} entities from database")

                    for row in rows:
                        entity = {
                            "id": row[0],
                            "level": row[1],
                            "name": row[2],
                            "type": row[3],
                            "parent_id": row[4],
                            "hierarchy_path": row[5],
                            "display_name": row[2]
                        }

                        if row[3] == "Brand":
                            if row[1] == 0:
                                entities_by_type["manufacturers"].append(entity)
                            elif row[1] == 1:
                                entities_by_type["brands"].append(entity)
                        elif row[3] == "Category":
                            if row[1] == 0:
                                entities_by_type["categories"].append(entity)
                            else:
                                entities_by_type["products"].append(entity)

                    logger.info(f"Categorized entities: "
                              f"{len(entities_by_type['manufacturers'])} manufacturers, "
                              f"{len(entities_by_type['brands'])} brands, "
                              f"{len(entities_by_type['categories'])} categories, "
                              f"{len(entities_by_type['products'])} products")

        except Exception as e:
            logger.error(f"Failed to extract entities: {e}")
            if not self.dry_run:
                raise
            logger.info("Dry run mode - using sample data")
            entities_by_type = self._get_sample_entities()

        return entities_by_type

    def _get_sample_entities(self) -> Dict[str, List[Dict]]:
        """Return sample entities for testing."""
        return {
            "manufacturers": [
                {"id": "MFR_001", "name": "Cadbury", "type": "manufacturer",
                 "display_name": "Cadbury"},
                {"id": "MFR_002", "name": "Thorntons", "type": "manufacturer",
                 "display_name": "Thorntons"},
                {"id": "MFR_003", "name": "Mars", "type": "manufacturer",
                 "display_name": "Mars"}
            ],
            "brands": [
                {"id": "BRD_001", "name": "Dairy Milk", "type": "brand",
                 "display_name": "Dairy Milk"},
                {"id": "BRD_002", "name": "Galaxy", "type": "brand",
                 "display_name": "Galaxy"},
                {"id": "BRD_003", "name": "Roses", "type": "brand",
                 "display_name": "Roses"}
            ],
            "categories": [
                {"id": "CAT_001", "name": "Chocolate Bars", "type": "category",
                 "display_name": "Chocolate Bars"},
                {"id": "CAT_002", "name": "Boxed Chocolates", "type": "category",
                 "display_name": "Boxed Chocolates"}
            ],
            "products": [
                {"id": "PRD_001", "name": "Milk Chocolate", "type": "product",
                 "display_name": "Milk Chocolate"},
                {"id": "PRD_002", "name": "Dark Chocolate", "type": "product",
                 "display_name": "Dark Chocolate"}
            ]
        }

    def generate_aliases(self, entities_by_type: Dict[str, List[Dict]]) -> List[Dict]:
        """Generate common aliases for each entity."""
        aliases = []

        for entity_type, entities in entities_by_type.items():
            for entity in entities:
                name = entity["name"]
                entity_id = entity["id"]

                variations = self._create_variations(name)

                for variation in variations:
                    aliases.append({
                        "type": entity_type.rstrip("s"),
                        "name": entity["display_name"],
                        "alias": variation,
                        "id": entity_id,
                        "confidence": 1.0 if variation == name.lower() else 0.9
                    })

        logger.info(f"Generated {len(aliases)} aliases from "
                   f"{sum(len(e) for e in entities_by_type.values())} entities")
        return aliases

    def _create_variations(self, name: str) -> Set[str]:
        """Create common variations of an entity name."""
        variations = set()

        variations.add(name.lower())

        variations.add(name.lower() + "s")
        variations.add(name.lower() + "'s")

        if " " in name:
            variations.add(name.lower().replace(" ", "_"))
            variations.add(name.lower().replace(" ", "-"))

        abbreviations = {
            "manufacturing": "mfg",
            "company": "co",
            "limited": "ltd",
            "incorporated": "inc",
            "corporation": "corp"
        }

        lower_name = name.lower()
        for full, abbr in abbreviations.items():
            if full in lower_name:
                variations.add(lower_name.replace(full, abbr))

        if len(name) > 5:
            variations.add(name[:3].lower())

        return variations

    def build_gazetteer(self, entities_by_type: Dict[str, List[Dict]]) -> Dict:
        """Build gazetteer structure for entity matching."""
        gazetteer = {
            "entities": {},
            "metrics": [
                "revenue", "sales", "market share", "growth", "volume",
                "price", "promotion", "elasticity", "margin", "profit"
            ],
            "timewords": [
                "Q1", "Q2", "Q3", "Q4", "quarter", "month", "year",
                "YTD", "MTD", "QTD", "last", "previous", "current",
                "January", "February", "March", "April", "May", "June",
                "July", "August", "September", "October", "November", "December"
            ],
            "special_tokens": ["vs", "versus", "compare", "analyze", "show", "what", "how"]
        }

        for entity_type, entities in entities_by_type.items():
            gazetteer["entities"][entity_type] = [e["name"] for e in entities]

        return gazetteer

    def save_artifacts(self, gazetteer: Dict, aliases: List[Dict]):
        """Save artifacts to JSON files."""
        if self.dry_run:
            logger.info("Dry run mode - skipping file write")
            logger.debug(f"Would save gazetteer: {json.dumps(gazetteer, indent=2)[:500]}...")
            logger.debug(f"Would save {len(aliases)} aliases")
            return

        self.output_dir.mkdir(parents=True, exist_ok=True)

        with open(self.gazetteer_path, 'w') as f:
            json.dump(gazetteer, f, indent=2)
        logger.info(f"Saved gazetteer to {self.gazetteer_path} "
                   f"({self.gazetteer_path.stat().st_size / 1024:.1f} KB)")

        with open(self.aliases_path, 'w') as f:
            for alias in aliases:
                f.write(json.dumps(alias) + '\n')
        logger.info(f"Saved aliases to {self.aliases_path} "
                   f"({self.aliases_path.stat().st_size / 1024:.1f} KB)")

        total_size = ((self.gazetteer_path.stat().st_size +
                      self.aliases_path.stat().st_size) / (1024 * 1024))
        if total_size > 10:
            logger.warning(f"Total artifact size ({total_size:.1f} MB) exceeds 10MB target")

    def push_to_redis(self, gazetteer: Dict, aliases: List[Dict]) -> bool:
        """Push artifacts to Redis with TTL."""
        if not redis:
            logger.warning("Redis not available - skipping cache push")
            return False

        if self.dry_run:
            logger.info("Dry run mode - skipping Redis push")
            return True

        try:
            r = redis.Redis(
                host=os.getenv("REDIS_HOST", "localhost"),
                port=int(os.getenv("REDIS_PORT", 6379)),
                decode_responses=True
            )

            r.ping()

            r.setex("entity:gazetteer", timedelta(hours=24), json.dumps(gazetteer))
            logger.info("Pushed gazetteer to Redis with 24-hour TTL")

            aliases_json = json.dumps(aliases)
            r.setex("entity:aliases", timedelta(hours=24), aliases_json)
            logger.info("Pushed aliases to Redis with 24-hour TTL")

            return True

        except Exception as e:
            logger.error(f"Failed to push to Redis: {e}")
            return False

    def run(self, push_redis: bool = False):
        """Execute the artifact generation pipeline."""
        start_time = time.time()

        logger.info("Starting entity artifact generation")

        entities_by_type = self.extract_entities()

        aliases = self.generate_aliases(entities_by_type)

        gazetteer = self.build_gazetteer(entities_by_type)

        self.save_artifacts(gazetteer, aliases)

        if push_redis:
            self.push_to_redis(gazetteer, aliases)

        elapsed_time = time.time() - start_time
        logger.info(f"Artifact generation completed in {elapsed_time:.1f} seconds")

        if elapsed_time > 120:
            logger.warning(f"Generation time ({elapsed_time:.1f}s) exceeds 2-minute target")


def main():
    """Main entry point for the script."""
    parser = argparse.ArgumentParser(
        description="Generate entity artifacts from Databricks for live intent highlighting"
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Run without writing files or pushing to Redis"
    )
    parser.add_argument(
        "--push-redis",
        action="store_true",
        help="Push artifacts to Redis cache"
    )
    parser.add_argument(
        "--verbose",
        action="store_true",
        help="Enable verbose logging"
    )

    args = parser.parse_args()

    try:
        generator = EntityArtifactGenerator(
            dry_run=args.dry_run,
            verbose=args.verbose
        )
        generator.run(push_redis=args.push_redis)

    except KeyboardInterrupt:
        logger.info("Generation cancelled by user")
        sys.exit(1)
    except Exception as e:
        logger.error(f"Generation failed: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()