(require 'magit-remote)

(defun ppr-magit-read-remote-branch (prompt remote)
  (magit-completing-read prompt (magit-remote-list-branches remote)))

(defun ppr-magit-read-remote (prompt &optional exclude)
  (magit-completing-read prompt (magit-list-remotes)
                         (lambda (elt) (not (string= elt exclude)))))

(defun ppr-make-pull-request ()
  (interactive)
  (let* ((origin-remote (magit-read-remote "Base Remote"))
         (github-origin-remote (replace-regexp-in-string
                                "\\(https://github.com/\\\|git@github.com:\\)" ""
                                (magit-git-string "remote" "get-url" origin-remote)))
         (user-remote (ppr-magit-read-remote "User Remote" origin-remote))
         (github-user-remote (replace-regexp-in-string
                              "\\(https://github.com/\\\|git@github.com:\\)" ""
                              (magit-git-string "remote" "get-url" user-remote)))
         (current-branch (magit-get-current-branch))
         (origin-remote-branch
          (ppr-magit-read-remote-branch
           (format "Base remote branch on %s" origin-remote)
           origin-remote)))

    (if (yes-or-no-p
         (format "Push force current branch %s to user remote %s" current-branch user-remote))
        (magit-run-git-async
         "push" "-f" "-v"
         user-remote current-branch))

    (with-editor (magit-shell-command
                  (format "hub pull-request -b %s:%s -h %s:%s" github-origin-remote
                          origin-remote-branch github-user-remote current-branch)))))
