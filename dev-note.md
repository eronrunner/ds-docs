
# TODO
## Phase 1
- Optimize Validator in meta.py - **DONE**
- Mapping app's theme to the theme of Questionary - **DONE** - can not apply to placeholder
- Check str type and int type to specify steps to input value by Click and Questionary - **DONE**
- Handle auto increment for int type - **PENDING**
- Handle KeyInterruption for Click - **DONE**
- Handle context path for Click - **DONE**
- Logger log to file on top - **DONE**
- Fix FieldInfo Optional, but it has pattern and can not receive None value - **DONE**
- Default value if user doesn't input value and have no choices - **DONE**
## Phase 2
- Load docs from json file to view, confirm validate again for docs - **DONE**
- Show tables configured - display table's docs in console - **DONE**
- Update fields of docs - update directly on files
- Remove/Reset as default value for fields
- Optimize Validator and type check in meta.py
- Show tabulate with dict data - **DONE**

## Phase 3
- Run as application of console
- Remove configure-table
- load-ds-info and load-tables-info merge to load-docs
- configure-data-source and configure-tables merge to configure-docs
- Remove pretty_str

### Note
types.new_class(name, bases=(), kwds=None, exec_body=None)