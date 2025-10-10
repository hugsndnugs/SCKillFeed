import unittest

from sc_kill_feed import parse_actor_death


class ParseTest(unittest.TestCase):
    def test_example_line(self):
        line = "<2025-10-10T00:38:41.559Z> [Notice] <Actor Death> CActor::Kill: 'Vagabondy' [202153878531] in zone 'Hangar_SmallFront_GrimHEX_6589113285541' killed by 'Ponder_OG' [200146291288] using 'volt_smg_energy_01_black01_6589113021365' [Class volt_smg_energy_01_black01] with damage type 'ElectricArc' from direction x: -0.423347, y: -0.876556, z: -0.228969 [Team_ActorTech][Actor]"
        parsed = parse_actor_death(line)
        self.assertIsNotNone(parsed)
        victim, killer, weapon = parsed
        self.assertEqual(victim, 'Vagabondy')
        self.assertEqual(killer, 'Ponder_OG')
        self.assertEqual(weapon, 'volt_smg_energy_01_black01_6589113021365')


if __name__ == '__main__':
    unittest.main()
