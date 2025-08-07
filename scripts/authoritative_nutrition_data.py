#!/usr/bin/env python3
"""
Authoritative Child Nutrition Data
Real nutrition guidelines from authoritative sources for TinyTummy RAG database.
"""

AUTHORITATIVE_NUTRITION_DATA = [
    # US CDC Guidelines
    {
        "title": "CDC Infant Feeding Guidelines (0-6 months)",
        "content": "Breastfeeding is the best source of nutrition for most infants. Breast milk provides all the nutrients an infant needs for the first 6 months of life. If breastfeeding is not possible, use iron-fortified infant formula. Do not give cow's milk or other milk substitutes to infants under 12 months. Start solid foods around 6 months of age, when your baby shows signs of readiness. Signs include sitting up with support, good head control, opening mouth when food approaches, and ability to move food from front to back of mouth.",
        "source": "CDC",
        "region": "US",
        "age_group": "0-6 months",
        "topic": "feeding_guidelines",
        "url": "https://www.cdc.gov/nutrition/infantandtoddlernutrition/index.html"
    },
    {
        "title": "CDC Infant Feeding Guidelines (6-12 months)",
        "content": "At 6 months, start introducing solid foods while continuing to breastfeed or give formula. Start with single-ingredient foods like rice cereal, pureed fruits and vegetables. Introduce one new food every 3-5 days to watch for allergic reactions. Good first foods include iron-fortified cereals, pureed meats, and mashed fruits and vegetables. Avoid honey before 12 months due to risk of botulism. Continue breastfeeding or formula until at least 12 months.",
        "source": "CDC",
        "region": "US",
        "age_group": "6-12 months",
        "topic": "feeding_guidelines",
        "url": "https://www.cdc.gov/nutrition/infantandtoddlernutrition/index.html"
    },
    {
        "title": "CDC Growth Charts and Milestones",
        "content": "CDC growth charts are used to track a child's growth and development. These charts show the normal range of weight, height, and head circumference for children by age and gender. Growth charts help identify if a child is growing normally or if there might be a health concern. Regular check-ups with a pediatrician should include growth measurements. Growth patterns are more important than individual measurements.",
        "source": "CDC",
        "region": "US",
        "age_group": "0-5 years",
        "topic": "growth_charts",
        "url": "https://www.cdc.gov/growthcharts/"
    },
    
    # WHO Global Guidelines
    {
        "title": "WHO Infant and Young Child Feeding Guidelines",
        "content": "WHO recommends exclusive breastfeeding for the first 6 months of life. Breastfeeding should continue alongside complementary foods until 2 years or beyond. Complementary foods should be introduced at 6 months when the infant shows signs of readiness. Foods should be adequate, safe, and properly fed. Continue breastfeeding on demand, including night feeds. Complementary foods should be given 2-3 times per day at 6-8 months, 3-4 times per day at 9-11 months, and 4-5 times per day at 12-24 months.",
        "source": "WHO",
        "region": "WHO",
        "age_group": "0-2 years",
        "topic": "feeding_guidelines",
        "url": "https://www.who.int/health-topics/infant-and-young-child-feeding"
    },
    {
        "title": "WHO Child Growth Standards",
        "content": "WHO Child Growth Standards describe normal child growth from birth to 5 years. These standards are based on healthy, breastfed children from diverse ethnic backgrounds. The standards include weight-for-age, length/height-for-age, weight-for-length/height, and body mass index-for-age. Head circumference-for-age and arm circumference-for-age are also included. These standards help identify children who may be undernourished or overweight.",
        "source": "WHO",
        "region": "WHO",
        "age_group": "0-5 years",
        "topic": "growth_standards",
        "url": "https://www.who.int/tools/child-growth-standards"
    },
    
    # UK NHS Guidelines
    {
        "title": "NHS Baby Feeding Guidelines (0-6 months)",
        "content": "Breastfeeding is the healthiest way to feed your baby. Breast milk contains all the nutrients your baby needs for the first 6 months. If you cannot breastfeed, use infant formula. Do not give cow's milk, goat's milk, or sheep's milk as a drink until your baby is 12 months old. You can use them in cooking from 6 months. Start introducing solid foods around 6 months when your baby shows signs of readiness.",
        "source": "NHS",
        "region": "UK",
        "age_group": "0-6 months",
        "topic": "feeding_guidelines",
        "url": "https://www.nhs.uk/conditions/baby/weaning-and-feeding/"
    },
    {
        "title": "NHS Weaning Guidelines (6-12 months)",
        "content": "Start weaning around 6 months when your baby can sit up and hold their head steady. Begin with smooth, runny purees and gradually move to mashed foods. Good first foods include baby rice, pureed vegetables, and pureed fruits. Introduce one new food at a time to check for allergies. Avoid salty, sugary, or fatty foods. Continue breastfeeding or formula alongside solid foods. Offer 3 meals a day by 12 months.",
        "source": "NHS",
        "region": "UK",
        "age_group": "6-12 months",
        "topic": "feeding_guidelines",
        "url": "https://www.nhs.uk/conditions/baby/weaning-and-feeding/"
    },
    
    # Canadian Guidelines
    {
        "title": "Health Canada Infant Nutrition Guidelines",
        "content": "Health Canada recommends exclusive breastfeeding for the first 6 months. If breastfeeding is not possible, use iron-fortified infant formula. Start introducing solid foods around 6 months when your baby shows signs of readiness. Signs include sitting with support, good head control, and showing interest in food. Begin with iron-rich foods like iron-fortified cereals, pureed meats, and mashed legumes. Continue breastfeeding until 2 years or beyond.",
        "source": "Health Canada",
        "region": "Canada",
        "age_group": "0-12 months",
        "topic": "nutrition_guidelines",
        "url": "https://www.canada.ca/en/health-canada/services/food-nutrition/healthy-eating/infant-feeding.html"
    },
    
    # Indian Guidelines
    {
        "title": "ICMR Infant and Young Child Feeding Guidelines",
        "content": "ICMR recommends exclusive breastfeeding for the first 6 months of life. Breastfeeding should continue alongside complementary foods until 2 years. Start complementary feeding at 6 months with energy-dense, nutrient-rich foods. Good first foods include khichdi, mashed fruits, and pureed vegetables. Include iron-rich foods like green leafy vegetables and legumes. Avoid giving tea, coffee, or sugary drinks. Continue breastfeeding on demand.",
        "source": "ICMR",
        "region": "India",
        "age_group": "0-2 years",
        "topic": "feeding_guidelines",
        "url": "https://main.icmr.nic.in/sites/default/files/guidelines/Infant_and_Young_Child_Feeding_Guidelines.pdf"
    },
    
    # Australian Guidelines
    {
        "title": "Australian Infant Feeding Guidelines",
        "content": "The Australian Dietary Guidelines recommend exclusive breastfeeding for the first 6 months. If breastfeeding is not possible, use iron-fortified infant formula. Start introducing solid foods around 6 months when your baby shows signs of readiness. Begin with iron-rich foods like iron-fortified cereals, pureed meats, and mashed legumes. Introduce one new food every 2-3 days to check for allergies. Continue breastfeeding until 12 months or beyond.",
        "source": "Australian Government",
        "region": "Australia",
        "age_group": "0-12 months",
        "topic": "nutrition_guidelines",
        "url": "https://www.eatforhealth.gov.au/age-and-stage/infants"
    },
    
    # Iron Deficiency Prevention
    {
        "title": "Iron Requirements for Infants (6-12 months)",
        "content": "Infants 6-12 months need 11mg of iron daily. Iron-fortified cereals are an excellent source. Pureed meats, especially red meat, provide highly absorbable heme iron. Legumes like lentils and beans are good plant-based sources. Vitamin C helps with iron absorption, so serve iron-rich foods with fruits or vegetables. Signs of iron deficiency include pale skin, fatigue, and poor appetite. Regular check-ups should include iron status monitoring.",
        "source": "WHO",
        "region": "WHO",
        "age_group": "6-12 months",
        "topic": "nutrition_guidelines",
        "url": "https://www.who.int/health-topics/infant-and-young-child-feeding"
    },
    
    # Vitamin D Guidelines
    {
        "title": "Vitamin D Requirements for Infants",
        "content": "Infants need 400 IU of vitamin D daily. Breastfed infants should receive vitamin D supplements as breast milk is low in vitamin D. Formula-fed infants may not need supplements if they consume enough fortified formula. Vitamin D helps with calcium absorption and bone development. Signs of vitamin D deficiency include rickets, delayed growth, and muscle weakness. Consult your pediatrician about vitamin D supplementation.",
        "source": "CDC",
        "region": "US",
        "age_group": "0-12 months",
        "topic": "nutrition_guidelines",
        "url": "https://www.cdc.gov/nutrition/infantandtoddlernutrition/index.html"
    },
    
    # Food Allergy Prevention
    {
        "title": "Food Allergy Prevention Guidelines",
        "content": "Introduce common allergens like peanuts, eggs, and fish early (4-6 months) to reduce allergy risk. Start with small amounts and monitor for reactions. Signs of food allergy include hives, swelling, vomiting, and difficulty breathing. If your child has eczema or a family history of allergies, consult your pediatrician before introducing allergens. Continue breastfeeding while introducing solid foods as it may help prevent allergies.",
        "source": "CDC",
        "region": "US",
        "age_group": "4-12 months",
        "topic": "feeding_guidelines",
        "url": "https://www.cdc.gov/nutrition/infantandtoddlernutrition/index.html"
    },
    
    # Growth Monitoring
    {
        "title": "Growth Monitoring Guidelines",
        "content": "Monitor weight, length, and head circumference regularly. Plot measurements on WHO growth charts. Growth patterns are more important than individual measurements. Children should follow their growth curve. Sudden changes in growth pattern may indicate health problems. Regular check-ups should include growth measurements and developmental screening. Discuss any concerns about growth with your pediatrician.",
        "source": "WHO",
        "region": "WHO",
        "age_group": "0-5 years",
        "topic": "growth_standards",
        "url": "https://www.who.int/tools/child-growth-standards"
    },
    
    # Toddler Nutrition (1-2 years)
    {
        "title": "Toddler Nutrition Guidelines (1-2 years)",
        "content": "Toddlers need a variety of foods from all food groups. Offer 3 meals and 2-3 snacks daily. Include fruits, vegetables, whole grains, lean proteins, and dairy. Limit added sugars and salt. Toddlers may be picky eaters - this is normal. Continue offering new foods even if initially refused. Model healthy eating habits. Avoid giving large amounts of juice or sugary drinks. Water is the best beverage choice.",
        "source": "CDC",
        "region": "US",
        "age_group": "1-2 years",
        "topic": "nutrition_guidelines",
        "url": "https://www.cdc.gov/nutrition/infantandtoddlernutrition/index.html"
    },
    
    # Preschool Nutrition (2-5 years)
    {
        "title": "Preschool Nutrition Guidelines (2-5 years)",
        "content": "Preschoolers need balanced meals with foods from all food groups. Offer regular meals and snacks. Include colorful fruits and vegetables daily. Choose whole grains over refined grains. Include lean proteins like fish, poultry, beans, and eggs. Limit processed foods, added sugars, and salt. Encourage drinking water and milk. Model healthy eating and involve children in meal planning and preparation.",
        "source": "CDC",
        "region": "US",
        "age_group": "2-5 years",
        "topic": "nutrition_guidelines",
        "url": "https://www.cdc.gov/nutrition/infantandtoddlernutrition/index.html"
    }
]

def get_authoritative_data():
    """Return the authoritative nutrition data"""
    return AUTHORITATIVE_NUTRITION_DATA

if __name__ == "__main__":
    print(f"Loaded {len(AUTHORITATIVE_NUTRITION_DATA)} authoritative nutrition documents")
    for doc in AUTHORITATIVE_NUTRITION_DATA:
        print(f"- {doc['title']} ({doc['region']}, {doc['age_group']})") 