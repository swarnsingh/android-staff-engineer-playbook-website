'use strict';
// Pure, curated teaching frames. These are a model, not captured runtime output.
(function (root) {
  const step = (time, parent, name, avatar, thread, caption, lines, signal = '') => ({ time, parent, name, avatar, thread, caption, lines, signal });
  const scenes = {
    success: {
      title: 'Both requests succeed',
      description: 'Illustrative inputs: name waits 500ms; avatar waits 800ms. Requests are main-safe and non-blocking.',
      code: ['coroutineScope {', '    val name = async { fetchName() } // 500ms wait', '    val avatar = async { fetchAvatar() } // 800ms wait', '    val resolvedName = name.await()', '    val resolvedAvatar = avatar.await()', '    Profile(resolvedName, resolvedAvatar)', '}'],
      steps: [
        step('Before start', 'Not started', 'Not started', 'Not started', 'Ready for input', 'The UI owner is about to start one profile load. No request has started yet.', [0]),
        step('0ms · after requests start', 'Waiting for results', 'Suspended', 'Suspended', 'Available for UI events', 'Both requests start. Each reaches its suspending wait. Their waits no longer occupy the UI thread.', [1, 2], 'ui'),
        step('About 500ms', 'Waiting for avatar', 'Complete', 'Suspended', 'Brief continuation, then available', 'Name finishes first. The caller can obtain it, but still waits for the avatar. This is not simultaneous completion.', [3], 'ui'),
        step('About 800ms', 'Combining results', 'Complete', 'Complete', 'Brief result-handling work', 'Avatar finishes. Both await calls can now supply their values and the block constructs the profile.', [4, 5]),
        step('After completion', 'Complete', 'Complete', 'Complete', 'Available for UI events', 'The scope block and both children have completed. The caller receives the profile; no child request is left running.', [6])
      ]
    },
    cancel: {
      title: 'Owner is cleared',
      description: 'Chosen lifecycle event: navigation removes the destination and clears its ViewModel while both requests wait.',
      code: ['viewModelScope.launch {', '    coroutineScope {', '        val name = async { fetchName() }', '        val avatar = async { fetchAvatar() }', '        Profile(name.await(), avatar.await())', '    }', '} // Owner clearing cancels the load; children clean up.'],
      steps: [
        step('Before start', 'Not started', 'Not started', 'Not started', 'Ready for input', 'This scene uses a destination-scoped ViewModel. Its owner will actually be cleared, not merely made invisible.', [0]),
        step('0ms · after requests start', 'Waiting for results', 'Suspended', 'Suspended', 'Available for UI events', 'Both main-safe requests are waiting. Their cancellation boundary is the owning profile load.', [2, 3], 'ui'),
        step('300ms · owner cleared', 'Cancelling', 'Cancellation requested', 'Cancellation requested', 'Handles navigation', 'The destination is removed and its ViewModel cleared. Cancellation is requested down the parent-child links.', [0, 6], 'down'),
        step('Cancellation checks & cleanup', 'Waiting for children', 'Cleaning up', 'Cleaning up', 'Brief cleanup/continuation work', 'Cancellable waits observe the request without waiting for the original deadlines. Each child runs its cleanup. A CPU loop or blocking API needs its own cooperation.', [6]),
        step('After cleanup completes', 'Cancelled', 'Cancelled', 'Cancelled', 'Available for UI events', 'Only after both children finish does the parent complete cancellation. It does not deliver a successful profile.', [6])
      ]
    },
    failure: {
      title: 'Required avatar fails',
      description: 'Alternative input: avatar throws an I/O failure at 300ms, before name would finish at 500ms. Both are required.',
      code: ['coroutineScope {', '    val name = async { fetchName() } // 500ms wait', '    val avatar = async { failAvatarAfter(300) }', '    val resolvedName = name.await()', '    val resolvedAvatar = avatar.await()', '    Profile(resolvedName, resolvedAvatar)', '} // The failure is rethrown to the caller.'],
      steps: [
        step('Before start', 'Not started', 'Not started', 'Not started', 'Ready for input', 'The policy in this scene requires both results. The avatar input has been changed to fail after 300ms.', [0]),
        step('0ms · after requests start', 'Waiting for results', 'Suspended', 'Suspended', 'Available for UI events', 'Both children start. The parent is awaiting required data, not yet rendering a profile.', [1, 2], 'ui'),
        step('300ms · avatar throws', 'Cancelling after failure', 'Cancellation requested', 'Failed', 'Brief failure-handling work', 'The required child failure reaches the ordinary scope and requests sibling cancellation, even though the caller was awaiting name first.', [2, 3], 'down'),
        step('Sibling cleanup', 'Waiting for child cleanup', 'Cleaning up', 'Failed', 'Brief cleanup work', 'The name request cooperates with cancellation and cleans up. Failure propagation does not mean cleanup has already finished.', [3, 6]),
        step('After cleanup completes', 'Failed', 'Cancelled', 'Failed', 'Caller handles load failure', 'The scope throws to its caller after children finish. The app must decide how to represent that failed load; this model does not imply an unhandled app crash.', [6])
      ]
    },
    supervised: {
      title: 'Avatar is optional (handled at await)',
      description: 'Same failing input at 300ms. The avatar child really fails; supervision keeps the name running, and the caller turns the failure into a placeholder where it reads the result.',
      code: ['supervisorScope {', '    val name = async { fetchName() }            // required', '    val avatar = async { failAvatarAfter(300) } // optional', '    val resolvedName = name.await()', '    val resolvedAvatar = try { avatar.await() }', '        catch (e: IOException) { null }         // fallback here', '    Profile(resolvedName, resolvedAvatar)', '}'],
      steps: [
        step('Before start', 'Not started', 'Not started', 'Not started', 'Ready for input', 'The product now allows a profile without an avatar. This scene lets the avatar child fail for real and decides what that means where the result is read.', [0]),
        step('0ms · after requests start', 'Waiting for results', 'Suspended', 'Suspended', 'Available for UI events', 'Both requests start inside a supervisorScope. The block suspends at name.await().', [1, 2, 3], 'ui'),
        step('300ms · avatar child fails', 'Waiting for name', 'Suspended', 'Failed', 'Brief failure handling, then available', 'The avatar child fails with IOException. A supervisor does not cancel itself or the name sibling, so the name keeps loading. Under coroutineScope this same failure would have cancelled the name — see "Required avatar fails".', [2], 'ui'),
        step('About 500ms · name ready', 'Combining partial result', 'Complete', 'Failed', 'Brief result-handling work', 'name.await() returns. avatar.await() rethrows the stored IOException, which the try/catch at this line turns into null.', [3, 4, 5]),
        step('After completion', 'Complete with fallback', 'Complete', 'Fallback: null', 'Available for UI events', 'The caller receives a profile with a placeholder avatar. Catching inside the avatar child instead would also work — and then a plain coroutineScope is enough, because that child never fails.', [6, 7])
      ]
    }
  };
  const api = {
    scenes,
    frame(sceneId, position) {
      const scene = scenes[sceneId] || scenes.success;
      const index = Math.max(0, Math.min(scene.steps.length - 1, Number(position) || 0));
      return { scene, index, step: scene.steps[index] };
    }
  };
  if (typeof module !== 'undefined' && module.exports) module.exports = api;
  root.COROUTINE_MODEL = api;
})(typeof window === 'undefined' ? globalThis : window);
