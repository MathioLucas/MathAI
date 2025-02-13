#!/usr/bin/env python3
import os
import json
import tempfile
from pathlib import Path
from manim import *
from elevenlabs import generate, save
import openai
import subprocess
from typing import List, Dict

class MathScene(Scene):
    def __init__(self, steps: List[Dict], *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.steps = steps
    
    def construct(self):
        # Track position for new elements
        current_y = 3
        all_equations = []
        
        for step in self.steps:
            # Create equation
            eq = MathTex(step['equation'])
            eq.shift(UP * current_y)
            
            # Create explanation text
            explanation = Text(step['explanation'], font_size=24)
            explanation.next_to(eq, RIGHT, buff=0.5)
            
            # Animate appearance
            self.play(Write(eq))
            self.play(Write(explanation))
            
            # Store for later reference
            all_equations.append((eq, explanation))
            current_y -= 1
            
            # Add arrow pointing to next step if not last step
            if current_y > -3:
                arrow = Arrow(
                    start=eq.get_bottom(),
                    end=eq.get_bottom() + DOWN,
                    color=BLUE
                )
                self.play(Create(arrow))
                all_equations.append((arrow,))
            
            # Pause for narration
            self.wait(2)
        
        # Final pause
        self.wait(2)

class MathTutor:
    def __init__(self):
        self.openai_api_key = os.getenv("OPENAI_API_KEY")
        self.elevenlabs_api_key = os.getenv("ELEVENLABS_API_KEY")
        
        if not self.openai_api_key or not self.elevenlabs_api_key:
            raise ValueError("API keys for OpenAI and ElevenLabs are required")
        
        openai.api_key = self.openai_api_key
    
    def generate_explanation(self, question: str) -> List[Dict]:
        """Generate step-by-step explanation using GPT-4"""
        prompt = f"""
        Explain this math problem step by step:
        {question}
        
        Format your response as a JSON array with each step containing:
        1. equation: The mathematical equation for this step
        2. explanation: A clear explanation of what's happening
        3. narration: Voice-over text for this step
        """
        
        response = openai.ChatCompletion.create(
            model="gpt-4",
            messages=[{"role": "user", "content": prompt}]
        )
        
        return json.loads(response.choices[0].message.content)
    
    def create_narration(self, steps: List[Dict]) -> str:
        """Generate voice narration using ElevenLabs"""
        # Combine all narration text
        full_narration = " ".join(step['narration'] for step in steps)
        
        # Generate audio
        audio = generate(
            text=full_narration,
            voice="Bella",  # Using a default voice
            model="eleven_multilingual_v1"
        )
        
        # Save to temporary file
        audio_path = "narration.mp3"
        save(audio, audio_path)
        return audio_path
    
    def create_video(self, question: str) -> str:
        """Create complete video explanation"""
        try:
            # 1. Generate explanation steps
            steps = self.generate_explanation(question)
            
            # 2. Create animation
            scene = MathScene(steps)
            scene_path = "math_scene.mp4"
            scene.render()
            
            # 3. Generate narration
            audio_path = self.create_narration(steps)
            
            # 4. Combine video and audio using ffmpeg
            output_path = "final_explanation.mp4"
            subprocess.run([
                'ffmpeg', '-y',
                '-i', scene_path,
                '-i', audio_path,
                '-c:v', 'copy',
                '-c:a', 'aac',
                output_path
            ])
            
            # Cleanup temporary files
            os.remove(scene_path)
            os.remove(audio_path)
            
            return output_path
            
        except Exception as e:
            print(f"Error creating video: {str(e)}")
            return None

def main():
    # Example usage
    tutor = MathTutor()
    
    question = input("Enter your math question: ")
    print("Generating video explanation...")
    
    video_path = tutor.create_video(question)
    
    if video_path:
        print(f"Explanation video created: {video_path}")
    else:
        print("Failed to create explanation video")

if __name__ == "__main__":
    main()
