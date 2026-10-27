# Review the private website build

This package was built by the private website repository's GitHub Actions workflow. `build-info.json` records its repository, commit and Actions run. It contains the static reader with relative links; it is not a live hosted site.

Unzip the package, open a terminal in the extracted directory, and run:

```sh
python3 -m http.server 4177 --bind 127.0.0.1 --directory site
```

Open `http://127.0.0.1:4177/`. Keep the server bound to localhost. Stop it with Ctrl-C when finished. All website changes belong in `swarnsingh/android-staff-engineer-playbook-website`, not in this generated package.

On GitHub, artifact access follows the private repository's permissions. Treat a downloaded copy as private too. The artifact is retained for 14 days; rerunning the workflow recreates it from the selected source commit. A remote private website still requires an owner-approved hosting runtime connected to the same repository.
