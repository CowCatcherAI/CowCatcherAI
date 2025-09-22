from ultralytics import YOLO
import cv2
import numpy as np
from PIL import Image
import torch
from transformers import AutoModelForCausalLM, AutoTokenizer
import warnings
import os

# Onderdruk HuggingFace waarschuwingen
warnings.filterwarnings("ignore", category=UserWarning)
os.environ["HF_HUB_DISABLE_SYMLINKS_WARNING"] = "1"

def get_mounting_detection_question():
    return """
You are a cattle reproduction specialist analyzing for estrus (heat) behavior in cows.

MOUNTING BEHAVIOR SIGNS TO CHECK:

📍 COW POSITIONING:
- One cow clearly elevated/raised above another cow
- Mounting cow's body is higher than surrounding cows
- Clear height difference between two cows

📍 LEG PLACEMENT:
- Front legs/hooves of one cow resting ON the back of another cow
- Hind legs of mounting cow still on ground, front legs elevated
- You may see hooves pressing into the mounted cow's back

📍 BODY POSTURE:
- Mounting cow's back is arched upward
- Head and neck of mounting cow positioned above/over another cow
- Mounted cow may have lowered head, supporting weight

📍 VIEWING ANGLES:
- From behind: You see rear legs on ground, cow's back elevated over another
- From side: Clear mounting position with one cow on top of another
- Front legs clearly visible on another cow's back/sides

❌ NOT MOUNTING:
- Cows simply standing close together at same height
- One cow just walking past another
- Cows grazing with heads down
- All cows at same ground level
- Cow standing in a cubicle and elevate footstep

QUESTION: Is one cow mounting (climbing on) another cow in this image? This indicates estrus/heat behavior.

ANSWER FORMAT: "YES - [describe the mounting position and which cow parts you see]" or "NO - [describe what you see instead]"
"""

class ImprovedYOLOMoondreamAgent:
    def __init__(self, yolo_model_path="yolov11.pt"):
        print("🔄 Laden van modellen...")
        
        # Load YOLO model
        print("📦 YOLO model laden...")
        self.yolo_model = YOLO(yolo_model_path)
        
        # Load Moondream model met error handling
        print("🌙 Moondream model laden...")
        try:
            self.moondream_model_id = "vikhyatk/moondream2"
            self.moondream_model = AutoModelForCausalLM.from_pretrained(
                self.moondream_model_id, 
                trust_remote_code=True,
                torch_dtype=torch.float16 if torch.cuda.is_available() else torch.float32,
                device_map="auto" if torch.cuda.is_available() else None
            )
            self.moondream_tokenizer = AutoTokenizer.from_pretrained(self.moondream_model_id)
            print("✅ Modellen succesvol geladen!")
            
            # Check GPU beschikbaarheid
            if torch.cuda.is_available():
                print(f"🚀 CUDA beschikbaar: {torch.cuda.get_device_name()}")
            else:
                print("💻 Draait op CPU (langzamer)")
                
        except Exception as e:
            print(f"❌ Fout bij laden Moondream: {e}")
            self.moondream_model = None
            self.moondream_tokenizer = None
    
    def expand_bbox(self, x1, y1, x2, y2, image_width, image_height, expansion_factor=0.2):
        """
        Vergroot de bounding box met een bepaalde factor (standaard 20%)
        maar blijft binnen de afbeeldingsgrenzen
        
        Args:
            x1, y1, x2, y2: Originele bounding box coördinaten
            image_width, image_height: Afmetingen van de originele afbeelding
            expansion_factor: Hoe veel de box moet worden uitgebreid (0.2 = 20%)
        
        Returns:
            Uitgebreide bounding box coördinaten
        """
        # Bereken de huidige breedte en hoogte van de bounding box
        bbox_width = x2 - x1
        bbox_height = y2 - y1
        
        # Bereken de uitbreiding in pixels
        expand_x = int(bbox_width * expansion_factor / 2)
        expand_y = int(bbox_height * expansion_factor / 2)
        
        # Pas de nieuwe coördinaten toe, maar blijf binnen de afbeeldingsgrenzen
        new_x1 = max(0, x1 - expand_x)
        new_y1 = max(0, y1 - expand_y)
        new_x2 = min(image_width, x2 + expand_x)
        new_y2 = min(image_height, y2 + expand_y)
        
        return new_x1, new_y1, new_x2, new_y2
    
    def describe_with_moondream(self, image, question=None):
        """Verbeterde Moondream beschrijving met error handling"""
        if self.moondream_model is None:
            return "Moondream model niet beschikbaar"
        
        # Use mounting detection question if no question provided
        if question is None:
            question = get_mounting_detection_question()
        
        try:
            # Resize image als het te groot is (voor snelheid)
            if image.size[0] > 512 or image.size[1] > 512:
                image.thumbnail((512, 512), Image.Resampling.LANCZOS)
            
            # Encode en beschrijf
            enc_image = self.moondream_model.encode_image(image)
            response = self.moondream_model.answer_question(
                enc_image, 
                question, 
                self.moondream_tokenizer
            )
            return response.strip()
            
        except Exception as e:
            return f"Beschrijving fout: {str(e)[:50]}..."
    
    def analyze_single_image(self, image_path, conf_threshold=0.4, max_detections=5, expansion_factor=0.2):
        """
        Analyseer enkele afbeelding met uitgebreide bounding boxes voor meer context
        
        Args:
            image_path: Pad naar de afbeelding
            conf_threshold: Minimale confidence score voor detecties
            max_detections: Maximaal aantal detecties om te analyseren
            expansion_factor: Hoe veel de bounding box moet worden uitgebreid (0.2 = 20%)
        """
        if not os.path.exists(image_path):
            print(f"❌ Bestand niet gevonden: {image_path}")
            return []
        
        print(f"🔍 Analyseren van: {image_path}")
        print(f"📐 Bounding box uitbreiding: {expansion_factor*100:.0f}%")
        
        # Load image
        try:
            image = cv2.imread(image_path)
            if image is None:
                print("❌ Kon afbeelding niet laden")
                return []
                
            image_rgb = cv2.cvtColor(image, cv2.COLOR_BGR2RGB)
            pil_image = Image.fromarray(image_rgb)
            image_width, image_height = pil_image.size
            print(f"📸 Afbeelding geladen: {pil_image.size}")
            
        except Exception as e:
            print(f"❌ Fout bij laden afbeelding: {e}")
            return []
        
        # Run YOLO prediction
        print("🎯 YOLO detectie uitvoeren...")
        results = self.yolo_model.predict(
            source=image_path, 
            conf=conf_threshold, 
            verbose=False,
            save=False
        )
        
        descriptions = []
        detection_count = 0
        
        for r in results:
            boxes = r.boxes
            if boxes is not None:
                print(f"🔍 {len(boxes)} detecties gevonden")
                
                for i, box in enumerate(boxes):
                    if detection_count >= max_detections:
                        print(f"⚠️  Maximaal {max_detections} detecties geanalyseerd")
                        break
                    
                    # Get original bounding box info
                    x1, y1, x2, y2 = box.xyxy[0].cpu().numpy().astype(int)
                    confidence = float(box.conf[0].cpu().numpy())
                    class_id = int(box.cls[0].cpu().numpy())
                    class_name = r.names[class_id]
                    
                    # Bewaar originele bbox voor annotatie
                    original_bbox = (x1, y1, x2, y2)
                    
                    # Vergroot de bounding box voor meer context
                    exp_x1, exp_y1, exp_x2, exp_y2 = self.expand_bbox(
                        x1, y1, x2, y2, 
                        image_width, image_height, 
                        expansion_factor
                    )
                    
                    print(f"\n📍 Detectie {detection_count + 1}:")
                    print(f"   Klasse: {class_name}")
                    print(f"   Confidence: {confidence:.2%}")
                    print(f"   Originele bbox: ({x1}, {y1}) → ({x2}, {y2})")
                    print(f"   Uitgebreide bbox: ({exp_x1}, {exp_y1}) → ({exp_x2}, {exp_y2})")
                    
                    # Crop met uitgebreide grenzen en valideer
                    try:
                        cropped_image = pil_image.crop((exp_x1, exp_y1, exp_x2, exp_y2))
                        if cropped_image.size[0] < 10 or cropped_image.size[1] < 10:
                            print("   ⚠️  Te klein om te analyseren")
                            continue
                        
                        print(f"   📏 Crop afmetingen: {cropped_image.size}")
                            
                        # Beschrijf met Moondream using mounting detection question
                        print("   🌙 Moondream mounting analyse met uitgebreide context...")
                        description = self.describe_with_moondream(cropped_image)
                        
                        detection_info = {
                            'class': class_name,
                            'confidence': confidence,
                            'bbox': original_bbox,  # Gebruik originele bbox voor annotatie
                            'expanded_bbox': (exp_x1, exp_y1, exp_x2, exp_y2),  # Bewaar ook uitgebreide bbox
                            'description': description,
                            'size': cropped_image.size,
                            'mounting_detected': description.upper().startswith('YES'),
                            'expansion_used': expansion_factor
                        }
                        
                        descriptions.append(detection_info)
                        print(f"   💬 Mounting analyse: {description[:100]}...")
                        detection_count += 1
                        
                    except Exception as e:
                        print(f"   ❌ Fout bij analyse: {e}")
                        continue
                
                print(f"\n✅ Analyse voltooid: {len(descriptions)} beschrijvingen gegenereerd")
        
        return descriptions
    
    def create_annotated_image(self, image_path, descriptions, output_path="annotated_output.jpg", show_expanded=False):
        """
        Maak een geannoteerde afbeelding met beschrijvingen
        
        Args:
            image_path: Pad naar originele afbeelding
            descriptions: Lijst met detectie beschrijvingen
            output_path: Waar de geannoteerde afbeelding wordt opgeslagen
            show_expanded: Als True, toon ook de uitgebreide bounding boxes
        """
        image = cv2.imread(image_path)
        
        for i, det in enumerate(descriptions):
            x1, y1, x2, y2 = det['bbox']
            
            # Kleur afhankelijk van mounting detectie
            color = (0, 255, 0) if det.get('mounting_detected', False) else (255, 255, 0)
            
            # Teken originele bounding box
            cv2.rectangle(image, (x1, y1), (x2, y2), color, 2)
            
            # Optioneel: teken ook de uitgebreide bbox in gestippelde lijn
            if show_expanded and 'expanded_bbox' in det:
                exp_x1, exp_y1, exp_x2, exp_y2 = det['expanded_bbox']
                # Teken gestippelde rechthoek voor uitgebreide bbox
                cv2.rectangle(image, (exp_x1, exp_y1), (exp_x2, exp_y2), color, 1)
            
            # Voeg tekst toe
            mounting_status = "🔴 MOUNTING" if det.get('mounting_detected', False) else "⚪ NO MOUNTING"
            label = f"{det['class']}: {mounting_status}"
            cv2.putText(
                image, 
                label, 
                (x1, max(y1-10, 10)), 
                cv2.FONT_HERSHEY_SIMPLEX, 
                0.6, 
                color, 
                2
            )
            
            # Voeg nummer toe
            cv2.putText(
                image, 
                str(i+1), 
                (x1+5, y1+20), 
                cv2.FONT_HERSHEY_SIMPLEX, 
                0.8, 
                (255, 255, 255), 
                2
            )
        
        cv2.imwrite(output_path, image)
        print(f"💾 Geannoteerde afbeelding opgeslagen: {output_path}")
        return output_path

# Test functie
def test_agent():
    """Test de agent met een voorbeeld"""
    print("🧪 Test van YOLO + Moondream Mounting Detection Agent")
    print("    met uitgebreide context (20% vergroting)")
    print("=" * 60)
    
    # Initialiseer agent
    agent = ImprovedYOLOMoondreamAgent("cowcatcherV14.pt")
    
    # Test met example.jpg (vervang door je bestand)
    image_path = "example3.jpg"
    
    if os.path.exists(image_path):
        # Analyseer met 20% uitgebreide bounding boxes
        descriptions = agent.analyze_single_image(
            image_path, 
            conf_threshold=0.7, 
            max_detections=5,
            expansion_factor=0.3  # 20% uitbreiding voor meer context
        )
        
        if descriptions:
            # Maak geannoteerde afbeelding (met optie om uitgebreide boxes te tonen)
            agent.create_annotated_image(
                image_path, 
                descriptions, 
                output_path="annotated_with_context.jpg",
                show_expanded=True  # Toon ook de uitgebreide boxes
            )
            
            # Print samenvatting
            print("\n📋 DETECTIE SAMENVATTING:")
            print("=" * 60)
            mounting_count = 0
            for i, det in enumerate(descriptions, 1):
                mounting_status = "🔴 MOUNTING DETECTED" if det.get('mounting_detected', False) else "⚪ No mounting"
                if det.get('mounting_detected', False):
                    mounting_count += 1
                    
                print(f"{i}. {det['class']} ({det['confidence']:.1%}) - {mounting_status}")
                print(f"   → Analyse met {det['expansion_used']*100:.0f}% uitgebreide context")
                print(f"   → {det['description']}")
                print()
            
            print(f"🎯 TOTAAL MOUNTING DETECTIES: {mounting_count}/{len(descriptions)}")
            
            if mounting_count > 0:
                print("\n⚠️  BELANGRIJK: Mounting gedrag gedetecteerd!")
                print("    Dit kan wijzen op oestrus/tochtigheid bij de koeien.")
            
        else:
            print("❌ Geen detecties gevonden")
            
    else:
        print(f"❌ Test bestand '{image_path}' niet gevonden")
        print("💡 Plaats een afbeelding genaamd 'example3.jpg' in deze map")

if __name__ == "__main__":
    test_agent()
