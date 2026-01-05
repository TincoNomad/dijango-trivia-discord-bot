from discord import Message, Client
from ..trivia_game import TriviaGame
from ..utils.logging_bot import command_logger
from api.settings import TRIVIA_URL
import json
import discord
from typing import List, Dict, Any

"""
Handles the creation of new trivia games.

This module manages the interactive process of creating new trivias including:
- Title validation
- Theme selection/creation
- Question/answer collection
- Difficulty setting
"""

class TriviaCreator:
    """
    Manages the interactive creation of new trivia games.
    
    Attributes:
        client (Client): Discord client instance
        trivia_game (TriviaGame): Game mechanics handler
    """

    def __init__(self, client: Client):
        self.client = client
        self.trivia_game = TriviaGame()

    def check_dm(self, message: Message) -> bool:
        """Verifica si el mensaje es un DM del usuario original"""
        return message.author == self.current_author and isinstance(message.channel, discord.DMChannel)

    async def handle_create_trivia(self, message: Message) -> None:
        """Handles the command to create a new trivia"""
        try:
            # Guardamos el autor actual para usarlo en check_dm
            self.current_author = message.author
            
            # Get title
            title = await self.get_valid_title(message.author)
            
            # Get theme
            theme_list, _ = await self.trivia_game.get_available_options()
            await message.author.send(
                f"Available themes:\n{theme_list}\n\n"
                "You can either select a theme by number or type a new theme name."
            )
            response = await self.client.wait_for('message', timeout=60.0, check=self.check_dm)

            # Check if response is a number (existing theme) or text (new theme)
            if response.content.isdigit():
                theme_num = int(response.content)
                if theme_num in self.trivia_game.theme_choices:
                    theme_data = self.trivia_game.theme_choices[theme_num]
                    theme = theme_data['name']
                else:
                    theme = response.content
                    await message.author.send(f"Creating new theme: {theme}")
            else:
                theme = response.content
                await message.author.send(f"Creating new theme: {theme}")

            # Get URL (optional)
            await message.author.send("Would you like to add a URL for this trivia? (yes/no)")
            url = None
            while True:
                response = await self.client.wait_for('message', timeout=60.0, check=self.check_dm)
                if response.content.lower() in ['yes', 'y']:
                    await message.author.send("Please enter the URL:")
                    response = await self.client.wait_for('message', timeout=60.0, check=self.check_dm)
                    url = response.content
                    break
                if response.content.lower() in ['no', 'n']:
                    break
                await message.author.send("Please answer 'yes' or 'no'")

            # Get difficulty
            await message.author.send("Select the difficulty (1-3):")
            def check_difficulty(m):
                return (m.author == message.author and 
                       isinstance(m.channel, discord.DMChannel) and 
                       m.content.isdigit() and 
                       1 <= int(m.content) <= 3)
            
            response = await self.client.wait_for('message', timeout=60.0, check=check_difficulty)
            difficulty = int(response.content)

            # Collect questions
            questions: List[Dict[str, Any]] = []
            await message.author.send("Now let's add the questions. You must add at least 3 questions.")
            await message.author.send("For each question, you'll need to add at least 2 answers.")

            while len(questions) < 3 or (len(questions) < 10):
                # Get question
                await message.author.send(f"\nQuestion #{len(questions) + 1}:")
                await message.author.send("Write the question:")
                response = await self.client.wait_for('message', timeout=60.0, check=self.check_dm)
                question_title = response.content

                # Collect answers for this question
                answers: List[Dict[str, Any]] = []
                has_correct_answer = False
                await message.author.send("\nNow add the answers. You need at least 2 answers and one must be correct.")

                while len(answers) < 2 or (len(answers) < 4):
                    await message.author.send(f"\nAnswer #{len(answers) + 1}:")
                    await message.author.send("Write the answer:")
                    response = await self.client.wait_for('message', timeout=60.0, check=self.check_dm)
                    answer_title = response.content

                    # Solo preguntamos si es la respuesta correcta si aún no hay una respuesta correcta
                    is_correct = False
                    if not has_correct_answer:
                        await message.author.send("Is this the correct answer? (yes/no)")
                        while True:
                            response = await self.client.wait_for('message', timeout=60.0, check=self.check_dm)
                            if response.content.lower() in ['yes', 'y']:
                                is_correct = True
                                has_correct_answer = True
                                break
                            if response.content.lower() in ['no', 'n']:
                                break
                            await message.author.send("Please answer 'yes' or 'no'")

                    answers.append({
                        "answer_title": answer_title,
                        "is_correct": is_correct
                    })

                    if len(answers) >= 2:
                        # Si ya tenemos 2 respuestas y una es correcta, podemos continuar
                        if has_correct_answer:
                            await message.author.send("Do you want to add another answer? (yes/no)")
                            while True:
                                response = await self.client.wait_for('message', timeout=60.0, check=self.check_dm)
                                if response.content.lower() in ['no', 'n']:
                                    break
                                if response.content.lower() in ['yes', 'y']:
                                    break
                                await message.author.send("Please answer 'yes' or 'no'")
                            if response.content.lower() in ['no', 'n']:
                                break
                        # Si no hay respuesta correcta aún, forzamos a continuar
                        elif len(answers) < 4:
                            await message.author.send("You need to mark one answer as correct. Let's continue with the next answer.")
                        else:
                            await message.author.send("You must mark one answer as correct before continuing.")
                            # Removemos la última respuesta para intentar de nuevo
                            answers.pop()

                questions.append({
                    "question_title": question_title,
                    "answers": answers
                })

                if len(questions) >= 3:
                    await message.author.send("Do you want to add another question? (yes/no)")
                    while True:
                        response = await self.client.wait_for('message', timeout=60.0, check=self.check_dm)
                        if response.content.lower() in ['no', 'n']:
                            break
                        if response.content.lower() in ['yes', 'y']:
                            break
                        await message.author.send("Please answer 'yes' or 'no'")
                    if response.content.lower() in ['no', 'n']:
                        break

            trivia_data = {
                "title": title,
                "theme": theme,
                "username": message.author.name,
                "difficulty": difficulty,
                "url": url,
                "questions": questions
            }

            # Agregar log detallado del JSON antes de enviarlo
            command_logger.info("Attempting to create trivia with data:")
            command_logger.info(json.dumps(trivia_data, indent=2))

            # Create trivia using API client
            async with self.trivia_game.api_client:
                try:
                    api_response = await self.trivia_game.api_client.post(
                        TRIVIA_URL,
                        trivia_data
                    )
                    
                    command_logger.info(f"API Response: {json.dumps(api_response, indent=2)}")
                    
                    if not api_response:
                        raise ValueError("Empty response from API")
                        
                    # Convertir la respuesta a diccionario si no lo es ya
                    response_data = (
                        api_response if isinstance(api_response, dict)
                        else json.loads(api_response)
                    )
                    
                    if not response_data.get('id'):
                        error_msg = response_data.get('error', 'Unknown error')
                        if "title" in response_data and "already exists" in str(response_data.get("title", [])):
                            # Si el error es por título duplicado, intentamos obtener un nuevo título
                            new_title = await self.get_valid_title(message.author)
                            trivia_data["title"] = new_title
                            # Intentamos crear la trivia nuevamente con el nuevo título
                            api_response = await self.trivia_game.api_client.post(
                                TRIVIA_URL,
                                trivia_data
                            )
                            response_data = (
                                api_response if isinstance(api_response, dict)
                                else json.loads(api_response)
                            )
                        else:
                            command_logger.error(f"API Error Response: {json.dumps(response_data, indent=2)}")
                            raise ValueError(f"Error creating trivia: {error_msg}")
                        
                except Exception as e:
                    command_logger.error("Error during trivia creation:")
                    command_logger.error(f"Data sent: {json.dumps(trivia_data, indent=2)}")
                    command_logger.error(f"Exception: {str(e)}")
                    raise

            # Send detailed summary via DM
            summary = [
                "✨ Trivia created successfully! Here's a summary:",
                f"\nTitle: {title}",
                f"Theme: {theme}",
                f"Difficulty: {difficulty}"
            ]
            
            if url:
                summary.append(f"URL: {url}")
                
            summary.append("\nQuestions:")

            for i, q in enumerate(questions, 1):
                summary.append(f"\n{i}. {q['question_title']}")
                for j, a in enumerate(q['answers'], 1):
                    correct = "✅" if a['is_correct'] else "❌"
                    summary.append(f"   {j}. {a['answer_title']} {correct}")

            await message.author.send("\n".join(summary))

        except TimeoutError:
            await message.author.send("Time's up for creating the trivia. Try again with $create_trivia")
        except Exception as e:
            command_logger.error(f"Error creating trivia: {e}")
            await message.author.send("An error occurred while creating the trivia. Please try again.")

    async def get_valid_title(self, author) -> str:
        """
        Gets a unique title for a new trivia.
        
        Args:
            author: Discord user creating the trivia
            
        Returns:
            str: Validated unique title
            
        Raises:
            TimeoutError: If user takes too long to respond
        """
        # Primero obtenemos y mostramos los títulos existentes
        existing_titles = set()
        async with self.trivia_game.api_client:
            try:
                existing_trivias = await self.trivia_game.api_client.get(TRIVIA_URL)
                if existing_trivias:
                    # Guardamos los títulos en un set para búsqueda rápida
                    existing_titles = {trivia['title'].lower() for trivia in existing_trivias}
                    
                    # Organizamos los títulos por tema
                    titles_by_theme: dict[str, list[str]] = {}
                    for trivia in existing_trivias:
                        theme = trivia.get('theme', 'Sin tema')
                        if theme not in titles_by_theme:
                            titles_by_theme[theme] = []
                        titles_by_theme[theme].append(trivia['title'])
                    
                    # Formateamos la lista organizada por temas
                    titles_list = ["**Existing trivia titles by theme:**"]
                    for theme, titles in titles_by_theme.items():
                        titles_list.append(f"\n__*{theme}*__")
                        for title in sorted(titles):
                            titles_list.append(f"• {title}")
                    
                    await author.send("\n".join(titles_list))
                    await author.send("\n⚠️ Please choose a different title from the ones listed above.")
            except Exception as e:
                command_logger.error(f"Error fetching existing trivias: {e}")
                await author.send("⚠️ Could not fetch existing titles, but you can continue creating your trivia.")
                pass

        while True:
            await author.send("\n Please enter a new title for your trivia:")
            def check_dm(m):
                return m.author == author and isinstance(m.channel, discord.DMChannel)
            
            response = await self.client.wait_for('message', timeout=60.0, check=check_dm)
            title = response.content

            # Verificar si el título ya existe en nuestra lista local
            if title.lower() in existing_titles:
                await author.send("❌ There is already a trivia with that title.")
                continue
            
            await author.send("✅ Title is available!")
            return title

"""
Handles active trivia game sessions.

This module manages the gameplay mechanics including:
- Question presentation
- Answer validation
- Score tracking
- Game state management
"""

class TriviaPlayer:
    """
    Manages active trivia game sessions and player interactions.
    
    Attributes:
        trivia_game (TriviaGame): Game mechanics handler
        game_state (GameState): Tracks active games
        client (Client): Discord client instance
    """

    async def _handle_game_start(self, message: Message):
        """
        Initiates a new game session.
        
        Args:
            message (Message): Discord message that triggered the game
        """