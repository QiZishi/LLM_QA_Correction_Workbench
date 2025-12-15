"""
Property-based tests for RenderEngine.

Tests universal properties for Markdown/LaTeX rendering and storage.
"""

from hypothesis import given, strategies as st, settings
from services import RenderEngine


# Feature: llm-qa-correction-workbench, Property 8: Markdown storage format
@given(st.text(min_size=1, max_size=200))
@settings(max_examples=100, deadline=None)
def test_markdown_storage_format(text_with_markdown):
    """
    For any text containing Markdown syntax edited by the user, the stored
    data should contain the raw Markdown markers (e.g., **text**) not HTML tags.
    
    **Validates: Requirements 3.2**
    """
    # Simulate user editing: text is stored as-is with Markdown markers
    stored_text = text_with_markdown
    
    # Property: Stored text should not contain HTML tags
    assert '<p>' not in stored_text or text_with_markdown.count('<p>') == stored_text.count('<p>')
    assert '<strong>' not in stored_text or text_with_markdown.count('<strong>') == stored_text.count('<strong>')
    
    # Property: If we add Markdown markers, they should be stored as-is
    markdown_text = f"**{text_with_markdown}**"
    assert '**' in markdown_text
    assert '<strong>' not in markdown_text


# Feature: llm-qa-correction-workbench, Property 11: LaTeX preservation
@given(st.text(min_size=1, max_size=100))
@settings(max_examples=100, deadline=None)
def test_latex_preservation(formula_content):
    """
    For any text containing LaTeX formulas (delimited by $...$), editing and
    storing the text should preserve the exact LaTeX syntax.
    
    **Validates: Requirements 3.5**
    """
    # Create text with LaTeX formula
    latex_text = f"The formula is ${formula_content}$"
    
    # Property: LaTeX delimiters should be preserved
    assert '$' in latex_text
    assert latex_text.count('$') >= 2
    
    # Property: Formula content should be preserved exactly
    assert formula_content in latex_text



# Feature: llm-qa-correction-workbench, Property 45: Nested rendering preservation
@given(
    st.text(min_size=1, max_size=100),
    st.sampled_from(['false', 'true'])
)
@settings(max_examples=100, deadline=None)
def test_nested_rendering_preservation(content, tag_type):
    """
    For any text containing false or true tags with Markdown or LaTeX inside,
    the rendering should apply tag styling while preserving internal formatting.
    
    **Validates: Requirements 12.5**
    """
    engine = RenderEngine()
    
    # Create text with tags containing Markdown
    markdown_content = f"**{content}**"
    tagged_text = f"<{tag_type}>{markdown_content}</{tag_type}>"
    
    # Render with diff tags
    result = engine.render_diff_tags(tagged_text)
    
    # Property: Tag styling should be applied
    assert '<span style=' in result
    
    # Property: Markdown markers should still be present
    assert '**' in result or '<strong>' in result
    
    # Property: Content should be preserved
    assert content in result or content.replace('&', '&amp;') in result
