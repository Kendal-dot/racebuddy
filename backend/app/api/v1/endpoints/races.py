from fastapi import APIRouter, HTTPException
from typing import List, Dict, Any
from core.schemas import RaceInfo

router = APIRouter()

# Hardcoded data for Lidingöloppet (later from RAG/database)
RACE_DATA = {
    "lidingo": RaceInfo(
        race_id="lidingo",
        name="Lidingöloppet",
        distance_km=30.0,
        location="Lidingö, Stockholm",
        description="""
        Lidingöloppet är en av Sveriges mest traditionsrika terrängtävlingar och en av hörnstenarna 
        i En Svensk Klassiker. Loppet går genom Lidingös varierade terräng med både skogspartier, 
        klippor och öppna marker. Med sina 30 kilometer och cirka 400 meters höjdskillnad 
        är det en utmaning som kräver både uthållighet och teknisk skicklighet.
        """.strip(),
        elevation_gain_m=400,
        typical_conditions="Höstväder, 5-15°C, risk för regn och blött underlag",
        key_challenges=[
            "Tekniska klipppartier runt kilometer 8-12",
            "Lång uppförsbacke vid kilometer 15",
            "Halt underlag vid regn",
            "Tät skog med rotiga stigar",
            "Mentalt krävande längd"
        ]
    )
}


@router.get("/", response_model=List[RaceInfo])
async def list_races():
    """List all available races"""
    return list(RACE_DATA.values())


@router.get("/{race_id}", response_model=RaceInfo)
async def get_race_info(race_id: str):
    """Get information about a specific race"""

    if race_id not in RACE_DATA:
        raise HTTPException(
            status_code=404,
            detail=f"Race '{race_id}' not found. Available races: {list(RACE_DATA.keys())}"
        )

    return RACE_DATA[race_id]


@router.get("/{race_id}/tips", response_model=Dict[str, Any])
async def get_race_tips(race_id: str):
    """Get training and race day tips for a specific race"""

    if race_id not in RACE_DATA:
        raise HTTPException(
            status_code=404, detail=f"Race '{race_id}' not found")

    # Hardcoded tips for Lidingöloppet
    tips = {
        "training_tips": [
            {
                "category": "Teknisk träning",
                "tip": "Träna regelbundet på teknisk terräng med rötter och stenar",
                "rationale": "Lidingöloppet har många tekniska sektioner som kräver vana"
            },
            {
                "category": "Backträning",
                "tip": "Inkludera långa, stadiga uppförsbackar i träningen",
                "rationale": "Loppet har flera längre klättringar som kräver god backstyrka"
            },
            {
                "category": "Långa pass",
                "tip": "Bygg upp till pass på 2-2.5 timmar för att hantera distansen",
                "rationale": "30km kräver god grunduthållighet och mental styrka"
            }
        ],
        "race_day_tips": [
            {
                "category": "Utrustning",
                "tip": "Använd terrängskor med bra grepp, även om det är torrt",
                "rationale": "Klipporna kan vara hala även utan regn"
            },
            {
                "category": "Taktik",
                "tip": "Hål igen de första 10km och spara energi till slutet",
                "rationale": "Många går ut för fort och får problem senare i loppet"
            },
            {
                "category": "Nutrition",
                "tip": "Ta med energi för minst 2.5 timmar, även om du siktar på snabbare tid",
                "rationale": "Teknisk terräng kan göra att du blir långsammare än planerat"
            }
        ],
        "weather_preparation": [
            {
                "condition": "Regn",
                "advice": "Extra försiktighet på klippor, kortare steg i tekniska partier"
            },
            {
                "condition": "Kallt väder",
                "advice": "Klä dig i lager, du kommer bli varm under loppet"
            },
            {
                "condition": "Vind",
                "advice": "Vindskydd kan behövas vid öppna partier, särskilt på Långängen"
            }
        ]
    }

    return tips


@router.get("/{race_id}/statistics", response_model=Dict[str, Any])
async def get_race_statistics(race_id: str):
    """Get historical statistics for a race"""

    if race_id not in RACE_DATA:
        raise HTTPException(
            status_code=404, detail=f"Race '{race_id}' not found")

    # Simulated statistics (later from real data)
    statistics = {
        "participation": {
            "average_participants": 15000,
            "completion_rate": 0.92,
            "growth_trend": "stable"
        },
        "finish_times": {
            "men": {
                "average": "2:45:30",
                "median": "2:42:15",
                "25th_percentile": "2:28:00",
                "75th_percentile": "3:05:00"
            },
            "women": {
                "average": "3:15:20",
                "median": "3:12:45",
                "25th_percentile": "2:55:00",
                "75th_percentile": "3:38:00"
            }
        },
        "age_groups": {
            "20-29": {"avg_time": "2:35:00", "participants": 2500},
            "30-39": {"avg_time": "2:42:00", "participants": 4200},
            "40-49": {"avg_time": "2:55:00", "participants": 4800},
            "50-59": {"avg_time": "3:12:00", "participants": 2800},
            "60+": {"avg_time": "3:45:00", "participants": 700}
        },
        "common_splits": {
            "10km": "52:30",
            "20km": "1:48:20",
            "25km": "2:18:45",
            "finish": "2:55:00"
        }
    }

    return statistics
