
#########
# aliases
from ._fs import (
    temporary_file,
    check_file,
    check_dir,
)
from ._misc import (
    check_name,
    parse_name_pattern,
    parse_tag_pattern,
    parse_selections,
)
from ._platform import (
    MS_WINDOWS,
    run_command,
)
from ._pyproject_toml import (
    parse_person,
    parse_classifier,
    parse_entry_point,
    parse_pyproject_toml,
    load_pyproject_toml,
)
from ._pythoninfo import (
    get_python_id,
    get_python_info,
)
