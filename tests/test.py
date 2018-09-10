import unittest
import bot

class TestBotCommands(unittest.TestCase):

    def test_handle_command(self):
        result = bot.handle_command("beets?")
        self.assertEqual(result, "I like 'em.")
        result = bot.handle_command("eggs?")
        self.assertEqual(result, "I like those too...")

if __name__ == '__main__':
    unittest.main()