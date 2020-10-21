;;; github-browse-remote.el --- Open github/gitlab from Emacs -*- lexical-binding:t -*-

;; Copyright © 2015-2020
;;
;; Author:     Chmouel Boudjnah
;; Version:    0.1.0
;; Keywords:   github
;; Package-Requires: ((s "1.9.0") (cl-lib "0.5"))

;; This program is free software: you can redistribute it and/or modify
;; it under the terms of the GNU General Public License as published by
;; the Free Software Foundation, either version 3 of the License, or
;; (at your option) any later version.

;; This program is distributed in the hope that it will be useful,
;; but WITHOUT ANY WARRANTY; without even the implied warranty of
;; MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
;; GNU General Public License for more details.

;; You should have received a copy of the GNU General Public License
;; along with this program.  If not, see <http://www.gnu.org/licenses/>.

;; This file is not part of GNU Emacs.

;;; Commentary:

;; Easily open target page on github, this uses the git-browse binary from here :
;; https://github.com/chmouel/chmouzies/blob/master/git/git-browse

;;; Code:

(require 's)
(require 'cl-lib)
(require 'vc-git)

(defgroup github-browse-remote nil
  "Open target on github/gitlab/bitbucket/stash/etc."
  :prefix "github-browse-remote-"
  :group 'applications)

(defcustom github-browse-remote-executable (executable-find "git-browse")
  "Path to the git-browse executable"
  :type 'string
  :group 'github-browse-remote)


(defcustom github-browse-remote-add-line-number-if-no-region-selected t
  "Always add line number even if region is not selected in buffer.
When is option is t, bar-browse adds line number to URL even if region was not selected.

By default is true."
  :type 'boolean
  :group 'github-browse-remote)


(defun github-browse-remote--call (path &optional master linestart lineend)
  (let ((start-line
         (when linestart
           (number-to-string (line-number-at-pos linestart))))
        (end-line
         (when lineend
           (number-to-string (line-number-at-pos lineend))))
        (default-directory
          (if (file-exists-p path)
              (file-name-directory path)
            default-directory
            )))
    (replace-regexp-in-string
     "\n$" ""
     (shell-command-to-string
      (concat
       github-browse-remote-executable
       (if master (concat " -m "))
       " -n " path
       (if start-line (concat " " start-line))
       (if end-line (concat " " end-line)))))))

(defun github-browse-remote-get-url (&optional master)
  "Main method, returns URL to browse."

  (cond
   ;; dired-mode
   ((eq major-mode 'dired-mode)
    (github-browse-remote--call (dired-current-directory) master))

   ;; magit-status-mode
   ((eq major-mode 'magit-status-mode)
    (github-browse-remote--call default-directory))

   ;; magit-log-mode
   ((or (eq major-mode 'magit-log-mode) (eq major-mode 'vc-annotate-mode))
    (github-browse-remote--call
     (save-excursion
       (save-restriction
         (widen)
         (goto-char (line-beginning-position))
         (search-forward " ")
         (buffer-substring-no-properties (line-beginning-position) (- (point) 1))))
     master))

   ;; magit-commit-mode and magit-revision-mode
   ((or (eq major-mode 'magit-commit-mode) (eq major-mode 'magit-revision-mode))
    (save-excursion
      ;; Search for the SHA1 on the first line.
      (goto-char (point-min))
      (let* ((first-line
              (buffer-substring-no-properties (line-beginning-position) (line-end-position)))
             (commithash (cl-loop for word in (s-split " " first-line)
                                  when (eq 40 (length word))
                                  return word)))
        (github-browse-remote--call commithash master))))

   ;; log-view-mode
   ((derived-mode-p 'log-view-mode)
    (github-browse-remote--call (cadr (log-view-current-entry)) master))

   ;; We're inside of file-attached buffer with active region
   ((and buffer-file-name (use-region-p))
    (let ((point-begin (min (region-beginning) (region-end)))
          (point-end (max (region-beginning) (region-end))))
      (github-browse-remote--call
       buffer-file-name master point-begin
       (if (eq (char-before point-end) ?\n) (- point-end 1) point-end))))

   ;; We're inside of file-attached buffer without region
   (buffer-file-name
    (let ((line (when github-browse-remote-add-line-number-if-no-region-selected (point))))
      (github-browse-remote--call (buffer-file-name) master line)))

   (t (error "Sorry, I'm not sure what to do with this."))))

;;;###autoload
(defun github-browse-remote ()
  "Browse the current file with `browse-url'."
  (interactive)
  (browse-url
   (github-browse-remote-get-url
    (when (consp current-prefix-arg) t))))

;;;###autoload
(defun github-browse-remote-kill ()
  "Add the URL of the current file to the kill ring.

Works like `github-browse-remote', but puts the address in the
kill ring instead of opening it with `browse-url'."
  (interactive)
  (kill-new
   (github-browse-remote-get-url
    (when (consp current-prefix-arg) t))))

(provide 'github-browse-remote)

;;; github-browse-remote.el ends here
