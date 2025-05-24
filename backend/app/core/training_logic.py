from datetime import date, timedelta
from typing import List, Dict, Any
from core.schemas import TrainingPlanRequest, WeekPlan, TrainingSession
import math
import logging

logger = logging.getLogger(__name__)

# Original training generator (fallback)


class TrainingPlanGenerator:
    """Generates training plans based on user data"""

    def __init__(self):
        # Basic training types
        self.session_types = {
            "easy_run": {
                "name": "Lugnt löppass",
                "description": "Lätt och behagligt tempo, bra för återhämtning",
                "intensity": "low"
            },
            "tempo_run": {
                "name": "Tempopass",
                "description": "Medelhårt tempo, ungefär som tävlingstempo",
                "intensity": "medium"
            },
            "interval_training": {
                "name": "Intervallträning",
                "description": "Hög intensitet med vila mellan intervaller",
                "intensity": "high"
            },
            "long_run": {
                "name": "Långpass",
                "description": "Långt pass för att bygga uthållighet",
                "intensity": "low-medium"
            },
            "hill_training": {
                "name": "Backträning",
                "description": "Träning i backar för att bygga styrka",
                "intensity": "medium-high"
            },
            "recovery_run": {
                "name": "Återhämtningspass",
                "description": "Mycket lätt jogging för aktiv återhämtning",
                "intensity": "very_low"
            }
        }

    def generate_plan(self, request: TrainingPlanRequest) -> Dict[str, Any]:
        """Generates a complete training plan"""

        # Calculate number of weeks
        training_weeks = self._calculate_training_weeks(
            request.start_date, request.race_date)

        # Determine weekly structure based on fitness level
        weekly_structure = self._get_weekly_structure(
            request.fitness_level,
            request.training_days_per_week
        )

        # Generate weeks
        weeks = []
        total_distance = 0

        for week_num in range(1, training_weeks + 1):
            week_plan = self._generate_week(
                week_number=week_num,
                total_weeks=training_weeks,
                start_date=request.start_date,
                request=request,
                weekly_structure=weekly_structure
            )
            weeks.append(week_plan)
            total_distance += week_plan.total_distance_km

        return {
            "weeks": weeks,
            "total_weeks": training_weeks,
            "total_distance_km": int(round(total_distance))
        }

    def _calculate_training_weeks(self, start_date: date, race_date: date) -> int:
        """Calculates number of training weeks"""
        delta = race_date - start_date
        weeks = delta.days // 7
        return max(4, min(20, weeks))  # Between 4-20 weeks

    def _get_weekly_structure(self, fitness_level: str, days_per_week: int) -> Dict[str, Any]:
        """Determines weekly structure based on fitness level"""

        base_structures = {
            "beginner": {
                3: ["easy_run", "easy_run", "long_run"],
                4: ["easy_run", "tempo_run", "easy_run", "long_run"],
                5: ["easy_run", "tempo_run", "easy_run", "recovery_run", "long_run"],
                6: ["easy_run", "tempo_run", "easy_run", "hill_training", "recovery_run", "long_run"],
                7: ["easy_run", "tempo_run", "easy_run", "interval_training", "easy_run", "recovery_run", "long_run"]
            },
            "intermediate": {
                3: ["tempo_run", "interval_training", "long_run"],
                4: ["easy_run", "tempo_run", "interval_training", "long_run"],
                5: ["easy_run", "tempo_run", "interval_training", "hill_training", "long_run"],
                6: ["easy_run", "tempo_run", "interval_training", "hill_training", "recovery_run", "long_run"],
                7: ["easy_run", "tempo_run", "easy_run", "interval_training", "hill_training", "recovery_run", "long_run"]
            },
            "advanced": {
                4: ["tempo_run", "interval_training", "hill_training", "long_run"],
                5: ["easy_run", "tempo_run", "interval_training", "hill_training", "long_run"],
                6: ["easy_run", "tempo_run", "interval_training", "hill_training", "tempo_run", "long_run"],
                7: ["easy_run", "tempo_run", "easy_run", "interval_training", "hill_training", "tempo_run", "long_run"]
            }
        }

        return base_structures[fitness_level][days_per_week]

    def _generate_week(self, week_number: int, total_weeks: int, start_date: date,
                       request: TrainingPlanRequest, weekly_structure: List[str]) -> WeekPlan:
        """Generates a week of training"""

        # Calculate week start date
        week_start = start_date + timedelta(weeks=week_number - 1)
        week_end = week_start + timedelta(days=6)

        # Determine week focus based on phase
        week_focus = self._determine_week_focus(week_number, total_weeks)

        # Calculate weekly volume
        base_distance = self._calculate_base_distance(
            request.fitness_level, request.target_time)
        week_distance = self._calculate_week_distance(
            week_number, total_weeks, base_distance, week_focus
        )

        # Generate sessions
        sessions = []
        session_dates = self._get_training_days(
            week_start, len(weekly_structure))

        for i, session_type in enumerate(weekly_structure):
            session = self._create_training_session(
                date=session_dates[i],
                session_type=session_type,
                week_focus=week_focus,
                total_week_distance=week_distance,
                session_index=i,
                total_sessions=len(weekly_structure)
            )
            sessions.append(session)

        return WeekPlan(
            week_number=week_number,
            start_date=week_start,
            end_date=week_end,
            focus=week_focus["name"],
            total_distance_km=week_distance,
            sessions=sessions
        )

    def _determine_week_focus(self, week_number: int, total_weeks: int) -> Dict[str, str]:
        """Determines week focus based on periodization"""
        progress = week_number / total_weeks

        if progress <= 0.3:  # First 30%
            return {
                "name": "Basbyggnad",
                "description": "Bygg upp grundkondition och löpvolym"
            }
        elif progress <= 0.7:  # 30-70%
            return {
                "name": "Styrka och fart",
                "description": "Utveckla löpkraft och hastighet"
            }
        elif progress <= 0.9:  # 70-90%
            return {
                "name": "Tävlingsförberedelse",
                "description": "Träna i tävlingstempo och finslipa formen"
            }
        else:  # Last 10%
            return {
                "name": "Avtrappning",
                "description": "Minska volymen och vila inför tävling"
            }

    def _calculate_base_distance(self, fitness_level: str, target_time: str) -> float:
        """Calculates base volume based on target level"""
        # Convert target time to minutes
        time_parts = target_time.split(':')
        target_minutes = int(time_parts[0]) * 60 + int(time_parts[1])

        # Base volume according to fitness level and target level
        base_distances = {
            "beginner": {"fast": 35, "medium": 30, "slow": 25},
            "intermediate": {"fast": 50, "medium": 45, "slow": 40},
            "advanced": {"fast": 70, "medium": 60, "slow": 55}
        }

        # Categorize target level (for 30km Lidingöloppet)
        if target_minutes < 150:  # Under 2:30
            speed_category = "fast"
        elif target_minutes < 210:  # 2:30-3:30
            speed_category = "medium"
        else:  # Over 3:30
            speed_category = "slow"

        return base_distances[fitness_level][speed_category]

    def _calculate_week_distance(self, week_number: int, total_weeks: int,
                                 base_distance: float, week_focus: Dict[str, str]) -> int:
        """Calculates weekly volume with periodization"""
        progress = week_number / total_weeks

        if progress <= 0.3:  # Base building - gradual increase
            multiplier = 0.7 + (progress * 1.0)  # 0.7 to 1.0
        elif progress <= 0.7:  # Peak phase
            # Peak around 1.15
            multiplier = 1.0 + \
                (0.3 * math.sin((progress - 0.3) * math.pi / 0.4))
        elif progress <= 0.9:  # Specific phase
            multiplier = 1.0
        else:  # Taper
            multiplier = 0.6  # Significantly reduce last week

        return int(round(base_distance * multiplier))

    def _get_training_days(self, week_start: date, num_sessions: int) -> List[date]:
        """Distributes training sessions across the week"""
        # Standard distribution: Monday, Wednesday, Friday, Saturday, Tuesday, Thursday, Sunday
        preferred_days = [0, 2, 4, 5, 1, 3, 6]  # Monday = 0

        training_days = []
        for i in range(num_sessions):
            day_offset = preferred_days[i % 7]
            training_days.append(week_start + timedelta(days=day_offset))

        return sorted(training_days)

    def _create_training_session(self, date: date, session_type: str, week_focus: Dict[str, str],
                                 total_week_distance: float, session_index: int,
                                 total_sessions: int) -> TrainingSession:
        """Creates a training session"""

        session_info = self.session_types[session_type]

        # Calculate session distance
        distance = self._calculate_session_distance(
            session_type, total_week_distance, session_index, total_sessions
        )

        # Generate description
        description = self._generate_session_description(
            session_type, session_info, distance, week_focus
        )

        # Calculate pace
        pace = self._calculate_pace(session_type, distance)

        return TrainingSession(
            date=date,
            type=session_info["name"],
            description=description,
            distance_km=distance,
            pace=pace,
            intensity=session_info["intensity"]
        )

    def _calculate_session_distance(self, session_type: str, total_week_distance: float,
                                    session_index: int, total_sessions: int) -> int:
        """Calculates distance for a training session"""

        # Distribution of weekly volume
        distribution = {
            "easy_run": 0.15,      # 15% of week
            "recovery_run": 0.10,   # 10% of week
            "tempo_run": 0.20,      # 20% of week
            "interval_training": 0.15,  # 15% of week
            "hill_training": 0.15,  # 15% of week
            "long_run": 0.35       # 35% of week
        }

        base_distance = total_week_distance * \
            distribution.get(session_type, 0.15)

        # Minimum and maximum distances
        if session_type == "long_run":
            return int(round(max(8, min(25, base_distance))))
        elif session_type == "recovery_run":
            return int(round(max(3, min(8, base_distance))))
        else:
            return int(round(max(4, min(15, base_distance))))

    def _calculate_pace(self, session_type: str, distance: float) -> str:
        """Calculates recommended pace"""

        # Base pace (will later be adapted to user's target level)
        base_paces = {
            "easy_run": "6:00",
            "recovery_run": "6:30",
            "tempo_run": "5:20",
            "interval_training": "4:50",
            "hill_training": "5:40",
            "long_run": "5:50"
        }

        return base_paces.get(session_type, "6:00")

    def _generate_session_description(self, session_type: str, session_info: Dict[str, str],
                                      distance: float, week_focus: Dict[str, str]) -> str:
        """Generates detailed description for training session"""

        base_description = session_info["description"]

        specific_descriptions = {
            "easy_run": f"Löp {distance} km i lugnt tempo. Fokusera på teknik och andning.",
            "recovery_run": f"Mycket lätt jogging {distance} km. Hjälper kroppen att återhämta sig.",
            "tempo_run": f"Löp {distance} km i medelhårt tempo, ungefär som din måltid i loppet.",
            "interval_training": f"Intervallträning totalt {distance} km. Växla mellan hög intensitet och vila.",
            "hill_training": f"Backträning {distance} km. Sök upp backar och träna löpkraft.",
            "long_run": f"Långpass {distance} km. Bygg uthållighet med stadigt tempo."
        }

        return specific_descriptions.get(session_type, f"{base_description} - {distance} km")


# AI-Enhanced Training Generator
class AIEnhancedTrainingPlanGenerator:
    """AI-enhanced training plan generator using RAG and agents"""

    def __init__(self):
        # Lazy import to avoid circular imports
        pass

    def generate_plan(self, request: TrainingPlanRequest) -> Dict[str, Any]:
        """Generates an AI-enhanced training plan"""

        try:
            # Lazy imports
            from core.rag.agents import race_buddy_agents
            from core.vector_store import vector_store

            # 1. Get race-specific information from RAG
            race_context = self._get_race_context(
                request.race.value, vector_store)

            # 2. Create AI prompt for training plan
            ai_prompt = self._create_training_plan_prompt(
                request, race_context)

            # 3. Generate training plan with AI
            ai_plan = self._generate_ai_training_plan(
                ai_prompt, race_buddy_agents)

            # 4. Structure the result
            structured_plan = self._structure_plan_data(ai_plan, request)

            return structured_plan

        except Exception as e:
            logger.error(f"Error generating AI training plan: {e}")
            # Fallback to simple plan if AI fails
            fallback_generator = TrainingPlanGenerator()
            return fallback_generator.generate_plan(request)

    def _get_race_context(self, race_name: str, vector_store) -> str:
        """Gets race-specific information from vector database"""
        try:
            # Search for race information
            race_query = f"{race_name} bana distans höjdmeter svårighetsgrad strategi"
            race_results = vector_store.query_race_data(
                race_query, n_results=3)

            # Search for training information
            training_query = f"{race_name} träning förberedelse terränglopp backar"
            training_results = vector_store.query_training_data(
                training_query, n_results=2)

            # Combine results
            context_parts = []

            if race_results:
                context_parts.append("LOPPINFORMATION:")
                for result in race_results:
                    context_parts.append(result['content'][:500])

            if training_results:
                context_parts.append("\nTRÄNINGSINFORMATION:")
                for result in training_results:
                    context_parts.append(result['content'][:500])

            return "\n\n".join(context_parts)

        except Exception as e:
            logger.error(f"Error getting race context: {e}")
            return f"Generell information om {race_name}: 30km terränglopp med cirka 400 höjdmeter."

    def _create_training_plan_prompt(self, request: TrainingPlanRequest, race_context: str) -> str:
        """Creates AI prompt for training plan"""

        # Calculate training period
        training_weeks = self._calculate_training_weeks(
            request.start_date, request.race_date)

        prompt = f"""Du är en expert löpträningscoach som ska skapa en MYCKET SPECIFIK träningsplan för Lidingöloppet.

ANVÄNDARINFORMATION:
- Kön: {request.gender.value}
- Ålder: {request.age} år
- Längd: {request.height_cm} cm
- Vikt: {request.weight_kg} kg
- Fitnessnivå: {request.fitness_level.value}
- Måltid: {request.target_time}
- Träningsdagar per vecka: {request.training_days_per_week}
- Träningsperiod: {training_weeks} veckor
- Startdatum: {request.start_date}
- Loppdatum: {request.race_date}

LOPPINFORMATION FRÅN DATABAS:
{race_context}

VIKTIGA INSTRUKTIONER:
1. Skapa en träningsplan med EXAKT {training_weeks} veckor
2. Varje vecka ska ha exakt {request.training_days_per_week} träningspass
3. Varje träningspass ska ha denna EXAKTA struktur:
   - "pass": Mycket specifik beskrivning (t.ex "5 km @ 6:30/km", "4 x 3 min uppför @ 6:45-7:00/km, joggvila", "2 km lätt jogg + 3 x 50 m stegring")
   - "fokus": Kort förklaring av syftet (t.ex "Lätt och behagligt", "Väcka fart utan slitage")
   - "distans_km": Exakt distans som siffra
   - "typ": Typ av pass (t.ex "Grundträning", "Intervall", "Längdpass")

4. Anpassa träningen för användarens fitnessnivå och måltid
5. Använd loppinformationen för att anpassa träningen (t.ex backträning för Lidingöloppets backar)
6. Variera träningen över veckorna med periodisering
7. Inkludera avtrappning sista veckorna före loppet

EXEMPEL PÅ RÄTT SVAR FÖR ETT TRÄNINGSPASS:
{{
  "pass": "5 km @ 6:30/km",
  "fokus": "Lätt och behagligt",
  "distans_km": 5.0,
  "typ": "Grundträning"
}}

EXEMPEL PÅ MER AVANCERAT PASS:
{{
  "pass": "4 x 3 min uppför @ 6:45-7:00/km, joggvila",
  "fokus": "Bygg kraft för Lidingöloppets backar",
  "distans_km": 6.0,
  "typ": "Backträning"
}}

Returnera träningsplanen som JSON med följande struktur:
{{
  "veckor": [
    {{
      "vecka": 1,
      "fokus": "Basbyggnad",
      "träningspass": [
        {{
          "dag": "måndag",
          "pass": "...",
          "fokus": "...",
          "distans_km": ...,
          "typ": "..."
        }}
      ]
    }}
  ]
}}
"""
        return prompt

    def _generate_ai_training_plan(self, prompt: str, race_buddy_agents) -> Dict[str, Any]:
        """Generates training plan with AI"""
        try:
            # Use training coach agent
            response = race_buddy_agents.chat(prompt)

            if response["success"]:
                # Try to parse JSON from response
                import json
                import re

                # Extract JSON from response
                content = response["response"]

                # Find JSON block in response
                json_match = re.search(r'\{.*\}', content, re.DOTALL)
                if json_match:
                    json_str = json_match.group()
                    return json.loads(json_str)
                else:
                    # If no JSON found, use entire response as text
                    return {"ai_response": content}
            else:
                raise Exception(
                    f"AI agent failed: {response.get('error', 'Unknown error')}")

        except Exception as e:
            logger.error(f"Error generating AI training plan: {e}")
            raise

    def _structure_plan_data(self, ai_plan: Dict[str, Any], request: TrainingPlanRequest) -> Dict[str, Any]:
        """Structures AI plan into our format"""

        weeks = []
        total_distance = 0

        # If AI returned structured plan
        if "veckor" in ai_plan:
            for week_data in ai_plan["veckor"]:
                week_sessions = []
                week_distance = 0

                # Calculate week start date
                week_start = request.start_date + \
                    timedelta(weeks=week_data["vecka"] - 1)

                # Create training sessions for the week
                training_days = self._get_training_days(
                    week_start, len(week_data["träningspass"]))

                for i, session_data in enumerate(week_data["träningspass"]):
                    session = TrainingSession(
                        date=training_days[i],
                        type=session_data.get("typ", "Träning"),
                        description=session_data.get("pass", "Träningspass"),
                        distance_km=session_data.get("distans_km", 5.0),
                        pace=self._extract_pace(session_data.get("pass", "")),
                        intensity=self._determine_intensity(
                            session_data.get("typ", "")),
                        notes=session_data.get("fokus", "")
                    )
                    week_sessions.append(session)
                    week_distance += session.distance_km or 0

                # Create week plan
                week_plan = WeekPlan(
                    week_number=week_data["vecka"],
                    start_date=week_start,
                    end_date=week_start + timedelta(days=6),
                    focus=week_data.get("fokus", "Träning"),
                    total_distance_km=week_distance,
                    sessions=week_sessions
                )

                weeks.append(week_plan)
                total_distance += week_distance

        # If AI didn't return structured plan, create fallback
        if not weeks:
            fallback_generator = TrainingPlanGenerator()
            return fallback_generator.generate_plan(request)

        return {
            "weeks": weeks,
            "total_weeks": len(weeks),
            "total_distance_km": int(round(total_distance))
        }

    def _extract_pace(self, pass_description: str) -> str:
        """Extracts pace from session description"""
        import re

        # Search for patterns like "@6:30/km" or "@ 6:30/km"
        pace_match = re.search(r'@\s*(\d+:\d+)/km', pass_description)
        if pace_match:
            return pace_match.group(1)

        # Search for patterns like "6:30-7:00/km"
        pace_range_match = re.search(
            r'(\d+:\d+)-(\d+:\d+)/km', pass_description)
        if pace_range_match:
            return f"{pace_range_match.group(1)}-{pace_range_match.group(2)}"

        return None

    def _determine_intensity(self, session_type: str) -> str:
        """Determines intensity based on session type"""
        intensity_map = {
            "Grundträning": "low",
            "Längdpass": "low-medium",
            "Tempoträning": "medium",
            "Intervall": "high",
            "Backträning": "medium-high",
            "Återhämtning": "very_low"
        }
        return intensity_map.get(session_type, "medium")

    def _get_training_days(self, week_start: date, num_sessions: int) -> List[date]:
        """Distributes training sessions across the week"""
        # Standard distribution: Monday, Wednesday, Friday, Saturday, Tuesday, Thursday, Sunday
        preferred_days = [0, 2, 4, 5, 1, 3, 6]  # Monday = 0

        training_days = []
        for i in range(num_sessions):
            day_offset = preferred_days[i % 7]
            training_days.append(week_start + timedelta(days=day_offset))

        return sorted(training_days)

    def _calculate_training_weeks(self, start_date: date, race_date: date) -> int:
        """Calculates number of training weeks"""
        delta = race_date - start_date
        weeks = delta.days // 7
        return max(4, min(20, weeks))


# Singleton instances
training_generator = TrainingPlanGenerator()
ai_training_generator = AIEnhancedTrainingPlanGenerator()
