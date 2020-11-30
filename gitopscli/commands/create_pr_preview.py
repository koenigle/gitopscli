from dataclasses import dataclass
from typing import Callable, Optional
from gitopscli.git import GitApiConfig, GitRepoApiFactory
from .create_preview import CreatePreviewCommand
from .command import Command


class CreatePrPreviewCommand(Command):
    @dataclass(frozen=True)
    class Args(GitApiConfig):
        git_user: str
        git_email: str

        organisation: str
        repository_name: str

        pr_id: int
        parent_id: Optional[int]

    def __init__(self, args: Args) -> None:
        self.__args = args

    def execute(self) -> None:
        _create_pr_preview_command(self.__args)


def _create_pr_preview_command(args: CreatePrPreviewCommand.Args) -> None:
    git_repo_api = GitRepoApiFactory.create(args, args.organisation, args.repository_name)

    pr_branch = git_repo_api.get_pull_request_branch(args.pr_id)
    git_hash = git_repo_api.get_branch_head_hash(pr_branch)

    add_pr_comment: Callable[[str], None] = lambda comment: git_repo_api.add_pull_request_comment(
        args.pr_id, comment, args.parent_id
    )

    create_preview_command = CreatePreviewCommand(
        args=CreatePreviewCommand.Args(
            username=args.username,
            password=args.password,
            git_user=args.git_user,
            git_email=args.git_email,
            organisation=args.organisation,
            repository_name=args.repository_name,
            git_provider=args.git_provider,
            git_provider_url=args.git_provider_url,
            git_hash=git_hash,
            preview_id=pr_branch,  # use pr_branch as preview id
        ),
    )
    create_preview_command.register_callbacks(
        deployment_already_up_to_date_callback=lambda route_host: add_pr_comment(
            f"The version `{git_hash}` has already been deployed. Access it here: https://{route_host}",
        ),
        deployment_updated_callback=lambda route_host: add_pr_comment(
            f"Preview environment updated to version `{git_hash}`. Access it here: https://{route_host}"
        ),
        deployment_created_callback=lambda route_host: add_pr_comment(
            f"New preview environment created for version `{git_hash}`. Access it here: https://{route_host}"
        ),
    )
    create_preview_command.execute()
