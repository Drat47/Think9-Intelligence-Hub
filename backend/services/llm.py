import os
import json
import re
from dotenv import load_dotenv

load_dotenv()

class LLMService:
    def __init__(self):
        self.use_mock = os.getenv("USE_MOCK_LLM", "true").lower() == "true"
        self.openai_key = os.getenv("OPENAI_API_KEY", "")
        self.gemini_key = os.getenv("GEMINI_API_KEY", "")
        
        # Initialize APIs if keys are present and mock is disabled
        if not self.use_mock:
            if self.openai_key:
                from openai import OpenAI
                self.client = OpenAI(api_key=self.openai_key)
            elif self.gemini_key:
                import google.generativeai as genai
                genai.configure(api_key=self.gemini_key)
                self.model = genai.GenerativeModel('gemini-pro')

    def generate(self, prompt: str, system_instruction: str = "") -> str:
        """Call configured LLM (OpenAI, Gemini) or use robust Mock fallback."""
        if self.use_mock or (not self.openai_key and not self.gemini_key):
            return self._mock_respond(prompt)
            
        try:
            if self.openai_key:
                response = self.client.chat.completions.create(
                    model="gpt-4o-mini",
                    messages=[
                        {"role": "system", "content": system_instruction},
                        {"role": "user", "content": prompt}
                    ],
                    temperature=0.2
                )
                return response.choices[0].message.content
                
            elif self.gemini_key:
                full_prompt = f"{system_instruction}\n\nUser Query: {prompt}"
                response = self.model.generate_content(full_prompt)
                return response.text
                
        except Exception as e:
            print(f"LLM API call failed, falling back to mock response. Error: {e}")
            return self._mock_respond(prompt)

    def _mock_respond(self, prompt: str) -> str:
        """Deterministic offline demo mode helper that reads context from prompt."""
        p_lower = prompt.lower()
        
        # --- Router Agent Prompt ---
        if "identify the brand and product names" in p_lower:
            brand = "null"
            product = "null"
            
            # Extract the raw user query inside the prompt
            query_match = re.search(r'query:\s*"([^"]+)"', p_lower)
            query_text = query_match.group(1).lower() if query_match else p_lower
            
            if "aura" in query_text:
                brand = "AURA"
                if "wash" in query_text or "hydrating" in query_text:
                    product = "Hydrating Face Wash"
            elif "nexa" in query_text:
                brand = "NEXA"
                if "blender" in query_text:
                    product = "Smart Blender"
            elif "viva" in query_text:
                brand = "VIVA"
                if "protein" in query_text or "powder" in query_text:
                    product = "Organic Protein Powder"
                    
            return json.dumps({
                "brand": brand,
                "product": product
            })
            
        # --- Analysis Agent Prompt ---
        if "analyze these customer complaints" in p_lower:
            # Extract brand and product
            if "aura" in p_lower:
                brand = "aura"
            elif "nexa" in p_lower:
                brand = "nexa"
            elif "viva" in p_lower:
                brand = "viva"
            else:
                brand = ""
                
            if "wash" in p_lower or "hydrating" in p_lower:
                product = "hydrating face wash"
            elif "blender" in p_lower:
                product = "smart blender"
            elif "powder" in p_lower or "protein" in p_lower:
                product = "organic protein powder"
            else:
                product = ""
            
            # Extract Negative_Feedbacks_Count
            count_match = re.search(r"current negative=(\d+)", p_lower)
            neg_count = int(count_match.group(1)) if count_match else 0
            
            finding = "General feedback is positive with no critical issues."
            issue_category = "General Operation"
            key_themes = ["satisfactory experience"]
            likely_causes = ["normal wear and tear"]
            trend = "UNKNOWN"
            supporting_evidence = []
            
            # Extract trend if printed in the prompt
            trend_match = re.search(r"trend=(\w+)", p_lower)
            if trend_match:
                trend = trend_match.group(1).upper()
                
            if neg_count > 0:
                if "aura" in brand:
                    finding = "Spike in packaging leakage and cap cracking incidents reported in the last 30 days."
                    issue_category = "Packaging & Quality Control"
                    key_themes = ["leaking bottles in transit", "broken flip-top caps", "ruined shipments"]
                    likely_causes = ["substandard cap plastics from supplier CapTech", "under-torque capping equipment"]
                    supporting_evidence = ["Spiked negative reviews", "Multiple support tickets for packaging leaks"]
                elif "nexa" in brand:
                    finding = "Motor base overheating and burnt plastic odor under heavy usage."
                    issue_category = "Hardware & Design Safety"
                    key_themes = ["blender base extremely hot", "smells like burning plastic", "automatic shutdown triggered"]
                    likely_causes = ["inadequate airflow in base housing", "high friction in blender bearing"]
                    supporting_evidence = ["Burnt smell customer feedback reports", "Automatic thermal shutdown logs"]
                elif "viva" in brand:
                    finding = "Protein powder fails to dissolve completely in cold liquids, leaving chalky residue."
                    issue_category = "Ingredients & Formulation"
                    key_themes = ["chalky clumps", "incomplete solubility in cold milk", "gritty texture"]
                    likely_causes = ["particle size too large for cold solubility", "insufficient emulsifiers in plant-based base"]
                    supporting_evidence = ["Customer complaints regarding solubility in almond milk"]
                
            return json.dumps({
                "finding": finding,
                "issue_category": issue_category,
                "key_themes": key_themes,
                "likely_causes": likely_causes,
                "trend": trend,
                "supporting_evidence": supporting_evidence
            })

        # --- Recommendation Agent Prompt ---
        if "final recommendation deck" in p_lower:
            # Extract brand/product
            if "aura" in p_lower:
                brand = "AURA"
            elif "nexa" in p_lower:
                brand = "NEXA"
            elif "viva" in p_lower:
                brand = "VIVA"
            else:
                brand = "Unknown"
                
            if "wash" in p_lower or "hydrating" in p_lower:
                product = "Hydrating Face Wash"
            elif "blender" in p_lower:
                product = "Smart Blender"
            elif "powder" in p_lower or "protein" in p_lower:
                product = "Organic Protein Powder"
            else:
                product = "Unknown"
                
            # Default empty recommendation structure
            finding_text = f"Reviewing performance for {brand} {product}."
            likely_causes = ["Indeterminate root cause due to lack of historical matches."]
            recommendations = ["Continue standard quality control monitoring."]
            confidence_level = "LOW"
            
            # Extract confidence level from prompt calculation
            conf_level_match = re.search(r"level=(\w+)", p_lower)
            if conf_level_match:
                confidence_level = conf_level_match.group(1).upper()
                
            # Extract Analysis findings from prompt
            findings_match = re.search(r"analysis findings:\s*([^\n\r]+)", p_lower)
            findings_text = findings_match.group(1).strip() if findings_match else ""
            
            if "leak" in findings_text.lower() or "cap" in findings_text.lower() or "packaging" in findings_text.lower():
                finding_text = f"Packaging leakage is the primary driver of negative feedback for {brand} {product}."
                likely_causes = ["Under-torque flip-top cap application (below 12 inch-pounds) and potential cap hinge embrittlement."]
                recommendations = [
                    "Perform immediate torque range check (target 12 to 18 inch-pounds) on the packaging lines.",
                    "Audit the current Polypropylene (PP) batch from CapTech Packaging Solutions for micro-cracks.",
                    "If defect rates persist, prepare a supplier transition plan to Apex Caps Ltd."
                ]
            elif "overheat" in findings_text.lower() or "motor" in findings_text.lower() or "burnt" in findings_text.lower():
                finding_text = f"Blender motor base overheating issues on heavy load cycles."
                likely_causes = ["Thermal overload triggered by insufficient housing ventilation or extended runtimes."]
                recommendations = [
                    "Redesign base ventilation slots to increase passive cooling flow.",
                    "Update product instruction manual to strongly warn against continuous high-speed usage exceeding 2 minutes.",
                    "Review motor supplier thermal tolerances."
                ]
            elif "dissolve" in findings_text.lower() or "solubility" in findings_text.lower() or "clump" in findings_text.lower():
                finding_text = f"Solubility issues and chalky texture in prepared beverages."
                likely_causes = ["Large raw material mesh size causing slow dissolution in cold liquids."]
                recommendations = [
                    "Instruct plant processing team to verify mesh size filtering limits.",
                    "Recommend on packaging label to mix or shake with room temperature liquid before cooling.",
                    "Evaluate addition of lecithin or other clean-label dispersion aids."
                ]
                
            return json.dumps({
                "finding": finding_text,
                "likely_causes": likely_causes,
                "recommendations": recommendations,
                "confidence_level": confidence_level
            })
            
        return "Deterministic offline demo mode response."

llm_service = LLMService()
