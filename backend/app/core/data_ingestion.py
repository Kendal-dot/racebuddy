import pandas as pd
import json
import logging
from pathlib import Path
from typing import List, Dict, Any
from datetime import datetime
import uuid

from core.vector_store import vector_store
from settings import settings

logger = logging.getLogger(__name__)


class LidingoDataIngestion:
    """Class for processing and importing Lidingöloppet CSV data into ChromaDB"""

    def __init__(self):
        self.csv_path = Path(settings.CSV_DATA_FILE)
        self.vector_store = vector_store

    def load_and_process_csv(self) -> pd.DataFrame:
        """Load and process the CSV file"""
        try:
            if not self.csv_path.exists():
                raise FileNotFoundError(f"CSV file not found: {self.csv_path}")

            # Read CSV file
            df = pd.read_csv(self.csv_path)
            logger.info(
                f"Loaded CSV with {len(df)} rows and {len(df.columns)} columns")

            # Log column names for debug
            logger.info(f"CSV columns: {list(df.columns)}")

            # Basic data cleaning
            df = df.dropna(how='all')  # Remove completely empty rows

            logger.info(f"After cleaning: {len(df)} rows")
            return df

        except Exception as e:
            logger.error(f"Error loading CSV: {e}")
            raise

    def create_race_documents(self, df: pd.DataFrame) -> List[Dict[str, Any]]:
        """Create documents from race data for the vector database"""
        documents = []

        try:
            # Group data by different categories

            # 1. Overall race statistics
            total_content = self._create_overview_content(df)
            documents.append({
                'content': total_content,
                'metadata': {
                    'type': 'race_overview',
                    'race': 'lidingo',
                    'data_source': 'scraped_web',
                    'created_at': datetime.now().isoformat()
                },
                'id': f"race_overview_{uuid.uuid4().hex[:8]}"
            })

            # 2. Detailed content analysis per URL (if URL column exists)
            if 'url' in df.columns and 'content' in df.columns:
                url_docs = self._create_url_documents(df)
                documents.extend(url_docs)

            # 3. Create thematic documents
            thematic_docs = self._create_thematic_documents(df)
            documents.extend(thematic_docs)

            logger.info(f"Created {len(documents)} documents from CSV data")
            return documents

        except Exception as e:
            logger.error(f"Error creating race documents: {e}")
            raise

    def _create_overview_content(self, df: pd.DataFrame) -> str:
        """Create overview content about the race"""
        content_parts = [
            "LIDINGÖLOPPET - COMPLETE RACE GUIDE AND INFORMATION",
            "",
            f"This guide is based on {len(df)} different sources from lidingoloppet.se"
        ]

        # If we have content column, summarize it
        if 'content' in df.columns:
            all_content = " ".join(df['content'].dropna().astype(str))

            # Extract keywords and phrases
            key_topics = self._extract_key_topics(all_content)
            if key_topics:
                content_parts.extend([
                    "",
                    "MAIN THEMES IN THE RACE:",
                    *[f"- {topic}" for topic in key_topics]
                ])

        # If we have title column, list important sections
        if 'title' in df.columns:
            titles = df['title'].dropna().unique()
            content_parts.extend([
                "",
                "IMPORTANT SECTIONS:",
                *[f"- {title}" for title in titles[:10]]  # Top 10
            ])

        return "\n".join(content_parts)

    def _create_url_documents(self, df: pd.DataFrame) -> List[Dict[str, Any]]:
        """Create documents for each URL with its content"""
        documents = []

        for idx, row in df.iterrows():
            if pd.notna(row.get('content')) and pd.notna(row.get('url')):
                content = str(row['content'])
                url = str(row['url'])
                title = str(row.get('title', 'Utan titel'))

                # Skip too short content
                if len(content) < 100:
                    continue

                # Format content
                formatted_content = f"""
SOURCE: {title}
URL: {url}

CONTENT:
{content}
                """.strip()

                documents.append({
                    'content': formatted_content,
                    'metadata': {
                        'type': 'url_content',
                        'race': 'lidingo',
                        'url': url,
                        'title': title,
                        'content_length': len(content),
                        'created_at': datetime.now().isoformat()
                    },
                    'id': f"url_{uuid.uuid4().hex[:8]}"
                })

        return documents

    def _create_thematic_documents(self, df: pd.DataFrame) -> List[Dict[str, Any]]:
        """Create thematic documents based on content type"""
        documents = []

        if 'content_type' in df.columns:
            # Group by content_type
            for content_type in df['content_type'].dropna().unique():
                type_df = df[df['content_type'] == content_type]

                if len(type_df) == 0:
                    continue

                # Combine all content for this type
                combined_content = []
                combined_content.append(
                    f"INFORMATION ABOUT: {content_type.upper()}")
                combined_content.append("")

                for idx, row in type_df.iterrows():
                    if pd.notna(row.get('content')):
                        title = row.get('title', 'Utan titel')
                        content = str(row['content'])

                        combined_content.append(f"--- {title} ---")
                        combined_content.append(content)
                        combined_content.append("")

                if len(combined_content) > 3:  # Only if we have real content
                    documents.append({
                        'content': "\n".join(combined_content),
                        'metadata': {
                            'type': 'thematic_content',
                            'race': 'lidingo',
                            'theme': content_type,
                            'source_count': len(type_df),
                            'created_at': datetime.now().isoformat()
                        },
                        'id': f"theme_{content_type}_{uuid.uuid4().hex[:8]}"
                    })

        return documents

    def _extract_key_topics(self, text: str) -> List[str]:
        """Extract key topics from text (simple implementation)"""
        # List of important terms for Lidingöloppet
        key_terms = [
            'anmälan', 'startinformation', 'resultat', 'praktisk information',
            'partners', 'nyheter', 'sportmässa', 'svenska klassiker',
            'cykling', 'simning', 'löpning', 'skidåkning',
            'vasaloppet', 'vätternrundan', 'vansbrosimningen',
            'träning', 'förberedelse', 'utrustning', 'nutrition',
            'väder', 'bana', 'höjdmeter', 'distans'
        ]

        text_lower = text.lower()
        found_topics = []

        for term in key_terms:
            if term in text_lower:
                found_topics.append(term.title())

        return found_topics[:10]  # Max 10 topics

    def create_training_guidelines(self) -> List[Dict[str, Any]]:
        """Create training guides based on Lidingöloppet"""
        training_docs = []

        # Basic training guides
        guidelines = [
            {
                'title': 'Grundträning för Lidingöloppet',
                'content': """
GRUNDTRÄNING FÖR LIDINGÖLOPPET (30KM TERRÄNGLOPP)

TRÄNINGSPERIOD: 12-20 veckor före loppet

GRUNDLÄGGANDE PRINCIPER:
- Bygg upp gradvis volym och intensitet
- 80% av träningen ska vara i låg intensitet
- 20% kan vara medium till hög intensitet
- Vila är lika viktigt som träning

VECKOSTRUKTUR:
- 3-4 träningspass per vecka för nybörjare
- 4-6 träningspass per vecka för erfarna
- Minst en vilodag mellan hårda pass

TRÄNINGSTYPER:
1. Grundträning (lätt jogging): 60-80% av träningen
2. Tempoträning (medel intensitet): 10-15% av träningen  
3. Intervallträning (hög intensitet): 5-10% av träningen
4. Lågpass (mycket lätt): 10-15% av träningen

SPECIFIKT FÖR LIDINGÖLOPPET:
- Träna regelbundet i terräng
- Öva backspring och backgång
- Träna balans och koordination på teknisk mark
- Bygg upp till 2-2.5 timmar längsta pass
                """,
                'topics': ['grundträning', 'periodisering', 'träningstyper']
            },
            {
                'title': 'Specifik träning för Lidingöloppets terräng',
                'content': """
TERRÄNGSPECIFIK TRÄNING FÖR LIDINGÖLOPPET

LIDINGÖLOPPETS UTMANINGAR:
- 30 km distans med ca 400 höjdmeter
- Tekniska klipppartier kilometer 8-12
- Lång uppförsbacke vid kilometer 15
- Halt underlag vid regn
- Tät skog med rotiga stigar

SPECIFIKA TRÄNINGSOMRÅDEN:

1. BACKTRÄNING:
- Korta, branta backar för kraft (30-60 sekunder)
- Långa, måttliga backar för uthållighet (3-8 minuter)
- Träna både uppför och nedför
- Fokus på teknik och effektivitet

2. TEKNISK TRÄNING:
- Träna på rötter, stenar och ojämn mark
- Balansträning på instabil yta
- Koordinationsövningar
- Träna med olika underlag (torrt/blött)

3. MENTALA FÖRBEREDELSER:
- Långa pass i tuff terräng
- Träna i olika väderförhållanden  
- Öva nutrition och vätskeintag under löpning
- Visualisering av loppet

REKOMMENDERADE TRÄNINGSPLATSER:
- Teknisk skogsterräng
- Klippiga områden (försiktigt!)
- Varierad terräng med både backar och flacka partier
                """,
                'topics': ['terrängträning', 'backträning', 'teknik', 'mental träning']
            },
            {
                'title': 'Tävlingsförberedelse och strategi',
                'content': """
TÄVLINGSFÖRBEREDELSE FÖR LIDINGÖLOPPET

3 VECKOR FÖRE LOPPET:
- Minska träningsvolymen gradvis
- Behåll intensiteten i små doser
- Fokus på återhämtning och hälsa
- Testa all utrustning

VECKAN FÖRE LOPPET:
- Lätta joggingpass, max 45-60 minuter
- 2-3 korta tempointervaller (håll kroppen vaken)
- Extra sömn och bra kost
- Undvik nya aktiviteter

LOPPSTRATEGI:

START (0-5 km):
- Starta försiktigt, låt kroppen värma upp
- Följ inte med i för högt tempo från start
- Spara energi för senare delen

MITTENDELEN (5-20 km):
- Hitta din rytm och håll den
- Var extra försiktig i tekniska partier
- Tänk på vätskeintag var 5:e km
- Använd energi vid uppmuntringsposter

SLUTDELEN (20-30 km):
- Här avgörs loppet - nu får du använda sparad energi
- Fokus på teknik även när du blir trött
- Positiv inställning och kämparglöd
- Tänk på målgång och känslan av att vara klar!

UTRUSTNING:
- Terrängskor med bra grepp
- Fungerande kläder (inga nya på loppdag!)
- Energi för 2.5-3 timmar
- Huvudbonad och handdukar vid växlingar
                """,
                'topics': ['tävlingsförberedelse', 'loppstrategi', 'utrustning', 'mental förberedelse']
            }
        ]

        for guide in guidelines:
            training_docs.append({
                'content': guide['content'],
                'metadata': {
                    'type': 'training_guide',
                    'race': 'lidingo',
                    'title': guide['title'],
                    # FIXED: Convert list to string
                    'topics': ', '.join(guide['topics']),
                    'created_at': datetime.now().isoformat()
                },
                'id': f"training_{uuid.uuid4().hex[:8]}"
            })

        return training_docs

    def ingest_all_data(self) -> Dict[str, Any]:
        """Main method for importing all data"""
        try:
            logger.info("Starting data ingestion process...")

            # 1. Load CSV data
            df = self.load_and_process_csv()

            # 2. Create race documents from CSV
            race_documents = self.create_race_documents(df)

            # 3. Create training guides
            training_documents = self.create_training_guidelines()

            # 4. Import race data to ChromaDB
            if race_documents:
                documents = [doc['content'] for doc in race_documents]
                metadatas = [doc['metadata'] for doc in race_documents]
                ids = [doc['id'] for doc in race_documents]

                self.vector_store.add_documents(
                    collection_name=self.vector_store.RACE_DATA_COLLECTION,
                    documents=documents,
                    metadatas=metadatas,
                    ids=ids
                )
                logger.info(f"Imported {len(race_documents)} race documents")

            # 5. Import training documents
            if training_documents:
                documents = [doc['content'] for doc in training_documents]
                metadatas = [doc['metadata'] for doc in training_documents]
                ids = [doc['id'] for doc in training_documents]

                self.vector_store.add_documents(
                    collection_name=self.vector_store.TRAINING_COLLECTION,
                    documents=documents,
                    metadatas=metadatas,
                    ids=ids
                )
                logger.info(
                    f"Imported {len(training_documents)} training documents")

            # 6. Return summary
            summary = {
                'status': 'success',
                'csv_rows_processed': len(df),
                'race_documents_created': len(race_documents),
                'training_documents_created': len(training_documents),
                'total_documents': len(race_documents) + len(training_documents),
                'timestamp': datetime.now().isoformat()
            }

            logger.info(f"Data ingestion completed successfully: {summary}")
            return summary

        except Exception as e:
            logger.error(f"Error during data ingestion: {e}")
            raise


# Singleton instance
data_ingestion = LidingoDataIngestion()
