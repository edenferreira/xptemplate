XPTemplate priority=lang

let [s:f, s:v] = XPTcontainer() 
 
XPTvar $TRUE          1
XPTvar $FALSE         0
XPTvar $NULL          NULL
XPTvar $UNDEFINED     NULL
XPTvar $INDENT_HELPER # nothing
XPTvar $IF_BRACKET_STL \n

XPTinclude 
      \ _common/common
      \ _common/personal


" ========================= Function and Variables =============================


" ================================= Snippets ===================================
XPTemplateDef 


XPT if hint=if\ ..:\ ..\ else...
XSET job=$INDENT_HELPER
if `cond^:
    `job^
``elif...`
{{^elif `cond2^:
    `job^
``elif...`
^`}}^`else...{{^else:
    `cursor^`}}^


XPT for hint=for\ ..\ in\ ..:\ ...
for `vars^ in `range^0)^:
    `cursor^


XPT def hint=def\ ..(\ ..\ ):\ ...
def `fun_name^( `params^^ ):
    `cursor^


XPT lambda hint=(labmda\ ..\ :\ ..)
(lambda `args^ : `expr^)


XPT try hint=try:\ ..\ except:\ ...
try:
    `what^
except `except^:
    `handler^`...^
except `exc^:
    `handle^`...^
`else...^else:
    \`\^^^
`finally...^finally:
   \`\^^^


XPT class hint=class\ ..\ :\ def\ __init__\ ...
class `className^ `inherit^^:
    def __init__( self `args^^):
        `cursor^


XPT ifmain hint=if\ __name__\ ==\ __main__
if __name__ == "__main__" :
  `cursor^

