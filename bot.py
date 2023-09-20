import discord
from discord.ext import commands


from game import get_game, Question
from pyopentdb import OpenTDBClient, Category, QuestionType, Difficulty


bot = commands.Bot(command_prefix="/", intents=discord.Intents.none())


@bot.event
async def on_ready():
    await bot.tree.sync()


@bot.tree.command(name="join")
async def join(interaction: discord.Interaction):
    new_game_state = get_game(interaction, create=True)

    if interaction.user.name not in new_game_state.scores:
        new_game_state.scores[interaction.user.name] = 0
        embed = discord.Embed(
            title="You joined the game!",
            color=discord.Color.green(),
            description="To start the game, do /start",
        )
    else:
        embed = discord.Embed(
            title="You already joined the game!",
            color=discord.Color.red(),
            description="To start the game, do /start",
        )

    await interaction.response.send_message(embed=embed)


@bot.tree.command(name="start")
@discord.app_commands.describe(amount="Amount of questions (DEFAULT 5)")
@discord.app_commands.choices(
    difficulty=[
        discord.app_commands.Choice(name="Easy", value=Difficulty.EASY.name),
        discord.app_commands.Choice(name="Medium", value=Difficulty.MEDIUM.name),
        discord.app_commands.Choice(name="Hard", value=Difficulty.HARD.name),
    ]
)
@discord.app_commands.choices(
    category=[
        discord.app_commands.Choice(
            name="Computer Science", value=Category.SCIENCE_COMPUTERS.name
        ),
        discord.app_commands.Choice(name="Animal", value=Category.ANIMALS.name),
    ]
)
async def start(
    interaction,
    amount: str = "5",
    difficulty: str = Difficulty.EASY.name,
    category: str = Category.SCIENCE_COMPUTERS.name,
):
    game_state = get_game(interaction)

    game_state.is_running = True

    client = OpenTDBClient()
    questions = client.get_questions(
        amount=int(amount),
        category=Category[category],
        difficulty=Difficulty[difficulty],
        question_type=QuestionType.TRUE_FALSE,
    )

    game_state.questions = [
        (Question(question.question, question.choices, question.answer))
        for question in questions
    ]

    await interaction.response.send_message(
        embed=get_question_embed(interaction, game_state)
    )

    # [(), (), (["True", "False"]), ()]


@bot.tree.command(name="answer")
@discord.app_commands.choices(
    answer=[
        discord.app_commands.Choice(name="T", value="True"),
        discord.app_commands.Choice(name="F", value="False"),
    ]
)
async def answer(interaction, answer: discord.app_commands.Choice[str]):
    game_state = get_game(interaction)

    embed = []

    if answer.value == game_state.get_current_question().answer:
        game_state.current_q_index += 1

        game_state.scores[interaction.user.name] += 1

        embed = [
            discord.Embed(
                title=f"{interaction.user.name} got the question right!!!",
                color=discord.Color.blurple(),
            ),
            get_question_embed(interaction, game_state),
        ]
    else:
        embed = [
            discord.Embed(
                title=f"{interaction.user.name} got the question WRONG!!!",
                color=discord.Color.red(),
            )
        ]

    # Sending multipkle embeds at once! embeds (not EMBED)
    await interaction.response.send_message(embeds=embed)
