from ckanext.better_stats.metrics import get_all_metrics


def define_env(env: object) -> None:
    """This is the hook for defining variables, macros and filters."""

    @env.macro
    def render_metric(metric_name: str) -> str:
        metrics = get_all_metrics()

        try:
            metric = metrics.get(metric_name)()  # type: ignore
        except Exception as e:  # noqa: BLE001
            return f"> [!WARNING]\n> Failed to instantiate '{metric_name}': {e}"

        title = metric.title
        desc = metric.description
        icon = metric.icon
        default_viz = metric.default_visualization.value
        supported_viz = [v.value for v in metric.supported_visualizations]
        docstring = metric.__doc__ or "No additional documentation."

        markdown = f"### {title}\n\n"
        markdown += f"{desc}\n\n"

        if docstring:
            markdown += "```\n"
            for line in docstring.split("\n"):
                markdown += f"{line.strip()}\n"
            markdown += "```\n\n"

        markdown += "| | |\n"
        markdown += "|---|---|\n"
        markdown += f"| **ID** | `{metric.name}` |\n"
        markdown += f"| **Icon** | `{icon}` |\n"
        markdown += f"| **Default Visualization** | `{default_viz}` |\n"
        markdown += f"| **Supported Visualizations** | {', '.join(f'`{v}`' for v in supported_viz)} |\n"
        markdown += (
            f"| **Supported Export Formats** | {', '.join(f'`{v}`' for v in metric.supported_export_formats)} |\n\n"
        )
        markdown += "---\n\n"

        return markdown
