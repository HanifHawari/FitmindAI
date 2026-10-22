"""Regression check for the catalogs used by dashboard, nutrition, and workout lists."""

import unittest
from unittest.mock import patch

from sqlalchemy import create_engine, func, select
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from database.catalog_seed import seed_catalogs
from database.db_models import Base, DBHealthyFood, DBMasterNutrition, DBProgramSummary, DBWorkout
from data_loader import search_programs


class CatalogSeedTests(unittest.TestCase):
    def test_empty_catalogs_are_seeded_once(self):
        engine = create_engine("sqlite://", connect_args={"check_same_thread": False}, poolclass=StaticPool)
        Base.metadata.create_all(engine)
        db_factory = sessionmaker(bind=engine)

        counts = seed_catalogs(db_factory)
        for name in ("nutrition", "programs", "workouts", "healthy_foods"):
            self.assertGreater(counts[name], 0, name)
        self.assertEqual(seed_catalogs(db_factory), {"nutrition": 0, "programs": 0, "workouts": 0, "healthy_foods": 0})
        with db_factory() as db:
            food = db.scalars(select(DBMasterNutrition)).first()
            program = db.scalars(select(DBProgramSummary)).first()
            workout = db.scalars(select(DBWorkout)).first()
            healthy = db.scalars(select(DBHealthyFood)).first()
            self.assertFalse(food.contains_gluten)
            self.assertEqual(food._food_name_lower, food.food_name.lower())
            self.assertIsNotNone(program._weeks_num)
            self.assertEqual(workout._body_part_lower, workout.body_part.lower())
            self.assertEqual(healthy._food_name_lower, healthy.food_name.lower())
            self.assertIsInstance(healthy.calories, float)
            for model, name in (
                (DBMasterNutrition, "nutrition"),
                (DBProgramSummary, "programs"),
                (DBWorkout, "workouts"),
                (DBHealthyFood, "healthy_foods"),
            ):
                self.assertEqual(db.scalar(select(func.count()).select_from(model)), counts[name])

        engine.dispose()

    def test_beginner_filter_includes_novice_programs(self):
        engine = create_engine("sqlite://", connect_args={"check_same_thread": False}, poolclass=StaticPool)
        Base.metadata.create_all(engine)
        db_factory = sessionmaker(bind=engine)
        with db_factory.begin() as db:
            db.add_all([
                DBProgramSummary(title="Pertama", level="['Beginner']"),
                DBProgramSummary(title="Kedua", level="['Novice']"),
                DBProgramSummary(title="Ketiga", level="['Advanced']"),
            ])
        with patch("data_loader.SessionLocal", db_factory):
            titles = {program["title"] for program in search_programs(level="Beginner")}
        self.assertEqual(titles, {"Pertama", "Kedua"})
        engine.dispose()


if __name__ == "__main__":
    unittest.main()
