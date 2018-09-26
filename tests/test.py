import unittest
import bot


class TestBotCommands(unittest.TestCase):

    def test_handle_command(self):
        result = bot.handle_command("-help")
        self.assertEqual(result, "Try these commands: sup? / nasa")


if __name__ == '__main__':
    unittest.main()
