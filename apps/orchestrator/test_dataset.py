"""
Test dataset for prompt evaluation: 5 diverse social media brands.
Each test case contains brand_memory input and golden-standard concepts.
"""

from datetime import datetime

TEST_CASES = [
    {
        "brand_id": "test-001-fitness",
        "brand_name": "FitFlow",
        "industry": "fitness & wellness",
        "brand_memory": {
            "brand": {
                "id": "test-001-fitness",
                "name": "FitFlow",
                "slug": "fitflow",
                "timezone": "UTC",
                "style_guide": "Modern, energetic, motivational. Bright color palette with greens and oranges. Minimalist design."
            },
            "profile": {
                "industry": "Fitness & Wellness",
                "description": "AI-powered fitness app targeting busy professionals who want quick, effective workouts",
                "location": "Newcastle, UK",
                "target_customer": "Professionals aged 25-45, health-conscious, short on time",
                "audience_age_range": "25-45",
                "audience_interests": "fitness, wellness, productivity, nutrition, mental health",
                "brand_colors": ["#00C853", "#FF6F00", "#FFFFFF", "#212121"],
                "typography": "Sans-serif, modern (Montserrat, Inter)",
                "photography_style": "Bright, energetic action shots. Real people working out. Minimal props. Natural lighting.",
                "tone": "Energetic, motivational, supportive, non-judgmental",
                "voice": "Casual, friendly, empowering",
                "brand_dna": ["energetic", "inclusive", "effective", "modern"],
                "things_i_like": "Real people, diversity, sweat/effort, progress moments, morning workouts",
                "things_i_dislike": "Overly posed looks, extreme body types, fake perfectionism",
                "visual_elements_to_avoid": "Cheesy gym clichés, filter-heavy images",
                "words_to_avoid": "burn, crush, pain, extreme",
                "avoid_neon": False,
                "avoid_clutter": True,
                "creativity_level": 2,
                "brand_consistency_level": 2,
                "reference_priority_level": 2,
                "content_diversity_level": 2,
            },
            "pillars": [
                {"id": "p1", "name": "Quick Workouts", "description": "5-30 minute sessions for busy schedules"},
                {"id": "p2", "name": "Nutrition Tips", "description": "Simple, practical eating advice"},
                {"id": "p3", "name": "Mindfulness", "description": "Meditation and mental wellness focus"},
            ],
            "products": [
                {"id": "prod1", "name": "FitFlow Premium", "category": "subscription", "description": "Unlimited AI-personalized workouts"},
                {"id": "prod2", "name": "Nutrition Guide", "category": "ebook", "description": "7-day clean eating plan"},
            ],
            "approval_history": [
                {"image_id": "img1", "headline": "Morning energy boost", "decision": "approved", "note": "Love the natural light and real person", "decided_at": datetime(2026, 9, 25)},
                {"image_id": "img2", "headline": "Stretching routine demo", "decision": "approved", "note": "Shows movement and effort", "decided_at": datetime(2026, 9, 24)},
                {"image_id": "img3", "headline": "Gym model posing", "decision": "rejected", "note": "Too posed and fake, not authentic", "decided_at": datetime(2026, 9, 23)},
                {"image_id": "img4", "headline": "Meditation in nature", "decision": "approved", "note": "Peaceful and on-brand", "decided_at": datetime(2026, 9, 22)},
            ],
        },
        "golden_concepts": [
            {
                "headline": "Morning movement ritual",
                "rationale": "Shows authentic morning routine with real person, aligns with 'Quick Workouts' pillar and audience's desire for achievable routines",
                "prompt": "Create an energetic social media image of a person doing a morning stretch routine in a bright, minimalist home space. Natural sunlight streaming through large windows. The person looks focused but relaxed, wearing simple athletic wear in green or orange tones. Show real effort and movement, not posed stillness. Minimalist background with white walls, wooden floor, single potted plant. Capture the transition from sleep to energy. Bright, clean composition with high contrast. No text overlay.",
                "content_pillar": "Quick Workouts",
                "product": ""
            },
            {
                "headline": "Nutrition truth: meal prep reality",
                "rationale": "Addresses practical wellness with 'Nutrition Tips' pillar; real food (not Instagram-perfect), relatable to busy professionals",
                "prompt": "Create an authentic social media image showing real meal prep in a modern kitchen. A person's hands arranging simple, healthy foods into containers: grilled chicken, rice, roasted vegetables in earth tones. Natural daylight. The scene feels practical and lived-in, not styled for magazines. Include fresh ingredients nearby (lime, herbs). Minimalist kitchen with white counters and natural wood. Emphasize simplicity and achievability over perfection. Bright, warm lighting. No text overlay.",
                "content_pillar": "Nutrition Tips",
                "product": "Nutrition Guide"
            },
            {
                "headline": "Mindful pause moment",
                "rationale": "Showcases 'Mindfulness' pillar with peaceful, inclusive imagery; contrasts with active workout content for diversity",
                "prompt": "Create a serene social media image of a person sitting cross-legged in a calm indoor space during meditation. Soft natural light, minimal distractions. They wear simple, comfortable clothing in neutral or soft colors. Perhaps a window view showing nature outside. Very subtle props: a small plant, a water bottle, a journal. The atmosphere is peaceful but grounded, not overly spiritual or ethereal. Clean, warm tones. Could show early morning or late afternoon light. No text overlay.",
                "content_pillar": "Mindfulness",
                "product": ""
            }
        ]
    },
    {
        "brand_id": "test-002-eco",
        "brand_name": "EcoHome",
        "industry": "sustainable home goods",
        "brand_memory": {
            "brand": {
                "id": "test-002-eco",
                "name": "EcoHome",
                "slug": "ecohome",
                "timezone": "UTC",
                "style_guide": "Natural, earthy, minimalist. Warm wood tones, sage green, cream. Organic shapes."
            },
            "profile": {
                "industry": "Sustainable Home Goods",
                "description": "Eco-friendly home products for environmentally conscious consumers",
                "location": "Portland, USA",
                "target_customer": "Millennials and Gen Z, sustainability-focused, design-conscious, 25-40",
                "audience_age_range": "25-40",
                "audience_interests": "sustainability, zero-waste living, minimalism, home decor, climate action",
                "brand_colors": ["#6B8E6F", "#E8DCC8", "#F5F1E8", "#3E4A3D"],
                "typography": "Mix of serif and sans-serif, organic feel (Georgia, Raleway)",
                "photography_style": "Warm, natural, lifestyle. Real homes, plant-forward. Soft, diffused lighting. Textured materials.",
                "tone": "Warm, educational, optimistic about sustainability",
                "voice": "Knowledgeable, approachable, inspiring",
                "brand_dna": ["sustainable", "authentic", "beautiful", "educational"],
                "things_i_like": "Plants, natural materials, real homes, people enjoying sustainable products, before/after transformations",
                "things_i_dislike": "Sterile product shots, greenwashing visuals, artificial perfection",
                "visual_elements_to_avoid": "Plastic, synthetic materials, harsh lighting, empty minimalism",
                "words_to_avoid": "eco-friendly (overused), green, save the planet",
                "avoid_neon": True,
                "avoid_clutter": True,
                "creativity_level": 2,
                "brand_consistency_level": 3,
                "reference_priority_level": 2,
                "content_diversity_level": 2,
            },
            "pillars": [
                {"id": "p1", "name": "Sustainable Living", "description": "Practical zero-waste and eco-conscious tips"},
                {"id": "p2", "name": "Product Stories", "description": "Where products come from and how they're made"},
                {"id": "p3", "name": "Home Inspiration", "description": "Design ideas for sustainable spaces"},
            ],
            "products": [
                {"id": "prod1", "name": "Bamboo Kitchen Set", "category": "kitchenware", "description": "100% sustainable bamboo utensils and storage"},
                {"id": "prod2", "name": "Linen Bedding", "category": "bedding", "description": "Organic linen sheets and pillowcases"},
                {"id": "prod3", "name": "Refill Station Bundle", "category": "home goods", "description": "Glass containers for bulk product refilling"},
            ],
            "approval_history": [
                {"image_id": "img1", "headline": "Bamboo kitchen transformation", "decision": "approved", "note": "Warm, inviting, shows real use", "decided_at": datetime(2026, 9, 24)},
                {"image_id": "img2", "headline": "Zero-waste bathroom setup", "decision": "approved", "note": "Beautiful and practical", "decided_at": datetime(2026, 9, 23)},
                {"image_id": "img3", "headline": "Linen bedding flat lay", "decision": "rejected", "note": "Too sterile and product-focused, not lifestyle", "decided_at": datetime(2026, 9, 22)},
            ],
        },
        "golden_concepts": [
            {
                "headline": "Bamboo kitchen in action",
                "rationale": "Directly features Bamboo Kitchen Set product while showcasing 'Sustainable Living' with warm, lived-in kitchen scenes that resonate with audience",
                "prompt": "Create a warm, lifestyle social media image of a person using bamboo kitchen utensils and storage in a bright, natural kitchen. Wood countertops, white or cream walls. Soft daylight from a window. Show the person reaching for or organizing items in bamboo containers. Fresh herbs, bread, or food nearby. The scene feels homey and real, not styled. Earth tones dominate. Include details: texture of bamboo, natural grain, warm wood tones. Convey both sustainability and beauty. No text overlay.",
                "content_pillar": "Product Stories",
                "product": "Bamboo Kitchen Set"
            },
            {
                "headline": "Bedroom sanctuary: linen luxury",
                "rationale": "Highlights Linen Bedding product and 'Home Inspiration' pillar; shows aspirational comfort without sterility",
                "prompt": "Create an inviting social media image of a serene bedroom with organic linen bedding in soft cream or sage tones. Warm, diffused morning light. A person is sitting on the bed or stretching, looking peaceful. Minimal decor: potted plants, simple wooden nightstand, perhaps an open window showing nature. The linens show natural wrinkles and texture, not perfect smoothness. Soft, warm color palette. Conveys comfort, sustainability, and personal sanctuary. No text overlay.",
                "content_pillar": "Home Inspiration",
                "product": "Linen Bedding"
            },
            {
                "headline": "Bulk refill ritual moment",
                "rationale": "Educates on 'Sustainable Living' with Refill Station Bundle; shows practical zero-waste action in relatable context",
                "prompt": "Create a detailed social media image of someone at home refilling personal care or household products from glass containers into smaller bottles. Natural lighting, warm tones. Show the Refill Station Bundle prominently: glass containers of various sizes, neatly organized on a shelf or counter. Natural wood shelving, minimal decor. Hands engaged in the refilling process. Convey the ease and beauty of zero-waste living. Warm, organic color palette with greens and creams. Textured details (glass, wood). No text overlay.",
                "content_pillar": "Sustainable Living",
                "product": "Refill Station Bundle"
            }
        ]
    },
    {
        "brand_id": "test-003-beauty",
        "brand_name": "GlowNature",
        "industry": "natural beauty",
        "brand_memory": {
            "brand": {
                "id": "test-003-beauty",
                "name": "GlowNature",
                "slug": "glownature",
                "timezone": "UTC",
                "style_guide": "Luxe but natural, botanical, golden and rose tones, dewy and fresh aesthetics"
            },
            "profile": {
                "industry": "Natural Beauty & Skincare",
                "description": "Clean beauty brand with natural, science-backed skincare",
                "location": "New York, USA",
                "target_customer": "Women 20-50, skincare enthusiasts, natural beauty advocates",
                "audience_age_range": "20-50",
                "audience_interests": "skincare, natural beauty, wellness, glow, clean ingredients, self-care",
                "brand_colors": ["#D4AF37", "#E8B4B4", "#F0EFE5", "#2C2C2C"],
                "typography": "Elegant serif with modern sans-serif accents (Playfair Display, Gotham)",
                "photography_style": "Dewy, glowing skin close-ups. Botanical elements. Soft, diffused light. Luxe but natural. Golden hour vibes.",
                "tone": "Luxurious, nurturing, confident, honest about ingredients",
                "voice": "Expert, warm, inclusive",
                "brand_dna": ["natural", "luxe", "honest", "glowing"],
                "things_i_like": "Dewy skin, botanical ingredients, diversity in skin tones, before/after glow, self-care rituals",
                "things_i_dislike": "Airbrushed perfection, unrealistic beauty standards, synthetic looks",
                "visual_elements_to_avoid": "Heavy makeup, filters, too much Photoshop",
                "words_to_avoid": "chemical, fake, toxin-free",
                "avoid_neon": True,
                "avoid_clutter": True,
                "creativity_level": 2,
                "brand_consistency_level": 2,
                "reference_priority_level": 3,
                "content_diversity_level": 2,
            },
            "pillars": [
                {"id": "p1", "name": "Skincare Rituals", "description": "Daily routines and application techniques"},
                {"id": "p2", "name": "Clean Ingredients", "description": "What's in our products and why it matters"},
                {"id": "p3", "name": "Skin Stories", "description": "Real customer transformations and testimonials"},
            ],
            "products": [
                {"id": "prod1", "name": "Golden Serum", "category": "serum", "description": "Vitamin C + botanical extracts for glow"},
                {"id": "prod2", "name": "Rose Hydration Mask", "category": "mask", "description": "Overnight plumping mask with rose petals"},
                {"id": "prod3", "name": "Starter Set", "category": "kit", "description": "Complete skincare routine in one box"},
            ],
            "approval_history": [
                {"image_id": "img1", "headline": "Dewy glow skin close-up", "decision": "approved", "note": "Beautiful, real, relatable", "decided_at": datetime(2026, 9, 25)},
                {"image_id": "img2", "headline": "Golden serum application", "decision": "approved", "note": "Shows the product beautifully", "decided_at": datetime(2026, 9, 24)},
                {"image_id": "img3", "headline": "Before/after transformation", "decision": "rejected", "note": "Too perfect, unrealistic, makes people feel bad", "decided_at": datetime(2026, 9, 23)},
            ],
        },
        "golden_concepts": [
            {
                "headline": "Glow ritual: morning refresh",
                "rationale": "Showcases 'Skincare Rituals' with relatable morning routine; emphasizes natural glow over perfection",
                "prompt": "Create a luxe yet natural social media image of a morning skincare routine. A person's hands applying serum or moisturizer to their glowing face. Soft, golden morning light. Minimal bathroom setting with white or soft neutral tones. Perhaps show the Golden Serum bottle nearby, with botanical elements (rose petals, leaves). The person's skin looks dewy and fresh, with subtle texture and reality (not airbrushed). Golden hour lighting that emphasizes natural glow. Luxe but achievable. No heavy makeup. No text overlay.",
                "content_pillar": "Skincare Rituals",
                "product": "Golden Serum"
            },
            {
                "headline": "Botanical beauty: rose essence",
                "rationale": "Educates on 'Clean Ingredients' through product story; visual emphasis on natural rose ingredient",
                "prompt": "Create an artistic social media image featuring the Rose Hydration Mask product with fresh rose petals, botanical elements. Show a close-up of the luxe product container with visible rose petals and natural ingredients. Perhaps a person applying it at night or holding the jar. Soft, diffused lighting with golden and rose tones. Include texture details: petals, glass container, product consistency. Luxe but natural aesthetic. Clean background with soft colors. Conveys both efficacy and natural beauty. No text overlay.",
                "content_pillar": "Clean Ingredients",
                "product": "Rose Hydration Mask"
            },
            {
                "headline": "Real skin radiance journey",
                "rationale": "Captures 'Skin Stories' with realistic transformation that inspires without setting unrealistic beauty standards",
                "prompt": "Create an honest social media image showing a person's skin before and after using the Starter Set, but with reality and natural lighting. Show the subtle improvements: clearer complexion, more radiant skin tone, healthier texture. Use consistent lighting for both images so comparison is fair and realistic. The person looks confident but natural, not airbrushed. Perhaps show them holding or displaying the Starter Set. Warm, honest lighting. Diverse skin tone representation. Focus on skin health, not perfection. No text overlay.",
                "content_pillar": "Skin Stories",
                "product": "Starter Set"
            }
        ]
    },
    {
        "brand_id": "test-004-food",
        "brand_name": "NourishBowl",
        "industry": "healthy food delivery",
        "brand_memory": {
            "brand": {
                "id": "test-004-food",
                "name": "NourishBowl",
                "slug": "nourishbowl",
                "timezone": "UTC",
                "style_guide": "Vibrant, appetite-focused, colorful ingredients, bright natural lighting, food-forward"
            },
            "profile": {
                "industry": "Healthy Food Delivery",
                "description": "AI-powered meal planning and delivery service for health-conscious busy professionals",
                "location": "Austin, USA",
                "target_customer": "Busy professionals 25-45 wanting healthy, convenient meals",
                "audience_age_range": "25-45",
                "audience_interests": "food, nutrition, health, convenience, meal prep, fitness, travel",
                "brand_colors": ["#FF6B35", "#4ECDC4", "#FFE66D", "#FFFFFF"],
                "typography": "Modern, friendly (Poppins, Source Sans Pro)",
                "photography_style": "Vibrant, colorful food close-ups. Overhead shots of bowls. Bright natural light. Human hands and meals. Real, appetizing.",
                "tone": "Energetic, approachable, health-focused, no diet-culture toxicity",
                "voice": "Friendly, encouraging, practical",
                "brand_dna": ["vibrant", "nourishing", "convenient", "accessible"],
                "things_i_like": "Colorful ingredients, diverse cuisines, real food, human enjoyment, variety, cultural foods",
                "things_i_dislike": "Bland green juice aesthetics, restrictive diet culture messaging, ultra-processed appearance",
                "visual_elements_to_avoid": "Fake garnishes, overly styled/unrealistic presentations",
                "words_to_avoid": "diet, cleanse, detox, guilt-free",
                "avoid_neon": False,
                "avoid_clutter": False,
                "creativity_level": 3,
                "brand_consistency_level": 2,
                "reference_priority_level": 2,
                "content_diversity_level": 3,
            },
            "pillars": [
                {"id": "p1", "name": "Flavor Stories", "description": "Cuisines and ingredient origins from around world"},
                {"id": "p2", "name": "Nutrition Transparency", "description": "Macros, benefits, ingredient sourcing"},
                {"id": "p3", "name": "Real People, Real Meals", "description": "Customer stories and actual meal experiences"},
            ],
            "products": [
                {"id": "prod1", "name": "Weekly Subscription", "category": "service", "description": "5 personalized meals weekly"},
                {"id": "prod2", "name": "Asian Fusion Collection", "category": "meal_bundle", "description": "3 Asian-inspired bowls per week"},
                {"id": "prod3", "name": "Macro-Flex Meals", "category": "customizable", "description": "Build your macros, pick your meals"},
            ],
            "approval_history": [
                {"image_id": "img1", "headline": "Vibrant Buddha bowl moment", "decision": "approved", "note": "Makes me want to eat it, real and appetizing", "decided_at": datetime(2026, 9, 25)},
                {"image_id": "img2", "headline": "Unboxing nourish experience", "decision": "approved", "note": "Shows real delivery and unpacking", "decided_at": datetime(2026, 9, 24)},
                {"image_id": "img3", "headline": "Green juice detox cleanse", "decision": "rejected", "note": "Tone-deaf, diet culture messaging not our brand", "decided_at": datetime(2026, 9, 23)},
            ],
        },
        "golden_concepts": [
            {
                "headline": "Rainbow bowl unveiling",
                "rationale": "Showcases 'Flavor Stories' with vibrant, appetite-inducing imagery; emphasizes variety and real enjoyment",
                "prompt": "Create a mouth-watering social media image of a colorful, ingredient-diverse NourishBowl. Overhead angle showing the complete meal: colorful vegetables, proteins, grains, sauces in different sections. Bright, natural sunlight creating shadows and depth. A person's hands holding or about to eat the bowl. Show real food textures and colors: reds, greens, oranges, yellows. Perhaps include a spoon or the person's face enjoying the meal. Vibrant, appetizing, but realistic. Clean white background or natural setting. No artificial garnishes. No text overlay.",
                "content_pillar": "Flavor Stories",
                "product": "Weekly Subscription"
            },
            {
                "headline": "Macro transparency: your custom bowl",
                "rationale": "Educates on 'Nutrition Transparency' with clear ingredient and nutritional focus; builds trust",
                "prompt": "Create an informative yet appetizing social media image showing the Macro-Flex meal customization. Display a bowl with clearly visible different ingredient categories (proteins, vegetables, grains, healthy fats) possibly with subtle labels or organized sections. Include a macro breakdown graphic or nutrition info subtly integrated. Bright, clear lighting. Show both the final meal and perhaps the ingredients separately. Convey customization and transparency. Vibrant colors of actual ingredients. Professional but accessible. No text overlay on the food itself.",
                "content_pillar": "Nutrition Transparency",
                "product": "Macro-Flex Meals"
            },
            {
                "headline": "Lunchtime joy: real person, real meal",
                "rationale": "Features 'Real People, Real Meals' pillar; shows authentic enjoyment and relatability without forced enthusiasm",
                "prompt": "Create a candid social media image of a real person enjoying their NourishBowl meal at home or office during lunchtime. Natural, unposed moment. They're eating, looking satisfied, perhaps at a desk with a drink nearby. The meal is the Macro-Flex or Asian Fusion Collection, colorful and appealing. Bright natural lighting. Show real eating moment, not a fake smile. Conveys nourishment, convenience, and genuine enjoyment. Diverse representation possible. Background feels real (office desk, home kitchen). No text overlay.",
                "content_pillar": "Real People, Real Meals",
                "product": "Asian Fusion Collection"
            }
        ]
    },
    {
        "brand_id": "test-005-fashion",
        "brand_name": "EthicalThreads",
        "industry": "sustainable fashion",
        "brand_memory": {
            "brand": {
                "id": "test-005-fashion",
                "name": "EthicalThreads",
                "slug": "ethical-threads",
                "timezone": "UTC",
                "style_guide": "Minimalist, timeless, neutrals with pops of color, quality fabrics, understated elegance"
            },
            "profile": {
                "industry": "Sustainable Fashion",
                "description": "Affordable, ethically-made clothing for conscious consumers who value quality and sustainability",
                "location": "Berlin, Germany",
                "target_customer": "Gen Z to Millennials 18-40, anti-fast-fashion, value authenticity and ethics",
                "audience_age_range": "18-40",
                "audience_interests": "fashion, sustainability, ethics, slow fashion, quality basics, cultural diversity",
                "brand_colors": ["#2C3E50", "#ECF0F1", "#E74C3C", "#95A5A6"],
                "typography": "Modern, minimal (Helvetica Neue, Lato)",
                "photography_style": "Authentic fashion photography. Real bodies, diverse models. Minimal styling. Focus on fabric and fit. Natural poses.",
                "tone": "Honest, inclusive, no greenwashing, educational about ethics",
                "voice": "Direct, thoughtful, relatable",
                "brand_dna": ["ethical", "timeless", "authentic", "inclusive"],
                "things_i_like": "Real bodies, diverse skin tones, people of all ages, quality basics, behind-the-scenes production, cultural dress",
                "things_i_dislike": "Unrealistic body standards, only thin models, overly styled looks, fast-fashion mentality",
                "visual_elements_to_avoid": "Excessive styling, artificial beauty, exclusivity vibes",
                "words_to_avoid": "eco-friendly, green, sustainable (overused), ethical (without proof)",
                "avoid_neon": True,
                "avoid_clutter": True,
                "creativity_level": 2,
                "brand_consistency_level": 3,
                "reference_priority_level": 2,
                "content_diversity_level": 3,
            },
            "pillars": [
                {"id": "p1", "name": "Behind the Seams", "description": "Production process, artisan stories, ethical sourcing"},
                {"id": "p2", "name": "Styling Tips", "description": "How to wear and restyle basics for longevity"},
                {"id": "p3", "name": "Community & Diversity", "description": "Real people wearing our clothes, diverse stories"},
            ],
            "products": [
                {"id": "prod1", "name": "Organic Cotton Essentials", "category": "basics", "description": "Timeless tees, shirts, basics in organic cotton"},
                {"id": "prod2", "name": "Fair-Trade Denim", "category": "bottoms", "description": "Ethically-made denim with transparent supply chain"},
                {"id": "prod3", "name": "Wardrobe Building Set", "category": "bundle", "description": "5-piece capsule wardrobe starter"},
            ],
            "approval_history": [
                {"image_id": "img1", "headline": "Denim on real bodies", "decision": "approved", "note": "Diverse, authentic, shows actual fit", "decided_at": datetime(2026, 9, 25)},
                {"image_id": "img2", "headline": "Artisan fair-trade production", "decision": "approved", "note": "Transparency builds trust", "decided_at": datetime(2026, 9, 24)},
                {"image_id": "img3", "headline": "Model wearing basics", "decision": "rejected", "note": "Too posed, doesn't feel authentic to our brand", "decided_at": datetime(2026, 9, 23)},
            ],
        },
        "golden_concepts": [
            {
                "headline": "Fair-Trade Denim: from source to wearer",
                "rationale": "Showcases 'Behind the Seams' pillar with transparency that builds trust; human-focused production story",
                "prompt": "Create a documentary-style social media image showing the Fair-Trade Denim journey. Could be split or sequential: artisans/workers in fair-trade facility hand-crafting denim, hands-on process, then a real person wearing the finished jeans in authentic pose (not model pose). Show actual denim fabric detail, stitching, quality. Mix of production and real-world wear. Natural, honest lighting. Include diverse people in production or wearing the jeans. Conveys ethics through authenticity, not just messaging. No text overlay.",
                "content_pillar": "Behind the Seams",
                "product": "Fair-Trade Denim"
            },
            {
                "headline": "Organic cotton, infinite styling",
                "rationale": "Features 'Styling Tips' pillar showing versatility of basics; promotes longevity mindset vs. fast fashion",
                "prompt": "Create an inspirational social media image showing one Organic Cotton Essential (e.g., a basic tee or shirt) styled in 3-4 different ways: casual, office, night out, weekend wear. Show the same piece with different bottoms, accessories, layers. Real person modeling in authentic poses, not runway-style. Neutral colors dominating with pops of color from accessories. Show the quality and longevity of the piece through repeated styling. Natural lighting, minimal background. Conveys timeless, investment-piece thinking. No text overlay.",
                "content_pillar": "Styling Tips",
                "product": "Organic Cotton Essentials"
            },
            {
                "headline": "Real people, real diversity, real wardrobes",
                "rationale": "Highlights 'Community & Diversity' pillar with inclusive representation; shows wardrobes work for real people",
                "prompt": "Create a diverse community-focused social media image featuring 2-3 people from different backgrounds, ages, body types wearing the Wardrobe Building Set basics together. Could be posed sitting or standing naturally (not model poses). Diverse skin tones, ages (18-60+), body types all represented. Show how the 5-piece capsule works for different people. Natural, honest poses and lighting. Minimal background, focus on the people and pieces. Conveys inclusion and belonging. Could show them styled differently. No text overlay.",
                "content_pillar": "Community & Diversity",
                "product": "Wardrobe Building Set"
            }
        ]
    }
]
